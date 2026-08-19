#!/usr/bin/env python3
"""
pocketcasts - upload a local audio/video file into Pocket Casts Files.

Pocket Casts has no published API. The endpoints and the protobuf field
numbers used here were read off Pocket Casts' own open-source iOS client
(Automattic/pocket-casts-ios): POST user/login for a bearer token, POST
files/upload/request to register the file and get back a presigned URL, then
PUT the bytes at that URL. Uploading requires a Plus or Patron account.

Because it is an undocumented interface, it can change without warning. When
it does, the failure will be an HTTP error from one of those two calls.

    python3 pocketcasts.py login                 # store a token
    python3 pocketcasts.py upload FILE [FILE...]
"""

from __future__ import annotations

import argparse
import getpass
import json
import mimetypes
import os
import shutil
import subprocess
import subprocess as sp
import sys
import time
import urllib.error
import urllib.request
import uuid as uuidlib
from pathlib import Path

API = "https://api.pocketcasts.com/"
KEYCHAIN_SERVICE = "ytqueue-pocketcasts"
STATE_DIR = Path("~/.local/state/ytqueue").expanduser()

CONTENT_TYPES = {
    ".mp3": "audio/mp3",
    ".m4a": "audio/mp4",
    ".aac": "audio/mp4",
    ".mp4": "video/mp4",
    ".m4v": "video/mp4",
    ".mov": "video/quicktime",
}


class PocketCastsError(Exception):
    pass


# --- just enough protobuf ---------------------------------------------------
#
# Only two message shapes are needed, so a full protobuf runtime would be a
# heavy dependency for what amounts to a dozen lines of varint encoding.
#
# FileUploadRequest:  1 uuid, 2 title, 3 size, 4 contentType, 5 duration,
#                     6 colour (Int32Value), 7 hasCustomImage
# FileUploadResponse: 1 uuid, 2 url


def _varint(n: int) -> bytes:
    if n < 0:
        raise ValueError("negative varint")
    out = bytearray()
    while True:
        b = n & 0x7F
        n >>= 7
        out.append(b | (0x80 if n else 0))
        if not n:
            return bytes(out)


def _tag(field: int, wire: int) -> bytes:
    return _varint((field << 3) | wire)


def _pb_string(field: int, value: str) -> bytes:
    raw = value.encode("utf-8")
    return _tag(field, 2) + _varint(len(raw)) + raw


def _pb_int(field: int, value: int) -> bytes:
    return _tag(field, 0) + _varint(int(value))


def _pb_bool(field: int, value: bool) -> bytes:
    return _tag(field, 0) + _varint(1 if value else 0)


def _pb_message(field: int, body: bytes) -> bytes:
    return _tag(field, 2) + _varint(len(body)) + body


def _pb_fields(data: bytes):
    """Walk a protobuf message, yielding (field_number, wire_type, value)."""
    i = 0
    while i < len(data):
        key, i = _read_varint(data, i)
        field, wire = key >> 3, key & 0x07
        if wire == 0:
            value, i = _read_varint(data, i)
        elif wire == 2:
            length, i = _read_varint(data, i)
            value, i = data[i:i + length], i + length
        elif wire == 5:
            value, i = data[i:i + 4], i + 4
        elif wire == 1:
            value, i = data[i:i + 8], i + 8
        else:
            raise PocketCastsError(f"unsupported protobuf wire type {wire}")
        yield field, wire, value


def _read_varint(data: bytes, i: int) -> tuple[int, int]:
    result = shift = 0
    while True:
        if i >= len(data):
            raise PocketCastsError("truncated protobuf response")
        b = data[i]
        i += 1
        result |= (b & 0x7F) << shift
        if not b & 0x80:
            return result, i
        shift += 7


def build_upload_request(file_uuid: str, title: str, size: int, content_type: str,
                         duration: int) -> bytes:
    return b"".join([
        _pb_string(1, file_uuid),
        _pb_string(2, title),
        _pb_int(3, size),
        _pb_string(4, content_type),
        _pb_int(5, max(0, int(duration))),
        _pb_message(6, b""),   # colour: Int32Value(0)
        _pb_bool(7, False),    # hasCustomImage
    ])


def parse_upload_response(data: bytes) -> str:
    for field, wire, value in _pb_fields(data):
        if field == 2 and wire == 2:
            return value.decode("utf-8")
    raise PocketCastsError("no upload URL in the server's response")


# --- http -------------------------------------------------------------------


def _request(url: str, *, data=None, headers=None, method=None, timeout=120):
    req = urllib.request.Request(url, data=data, method=method,
                                 headers=headers or {})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, resp.read()
    except urllib.error.HTTPError as exc:
        body = exc.read()[:400].decode("utf-8", "replace").strip()
        raise PocketCastsError(f"HTTP {exc.code} from {url}\n  {body}") from None
    except urllib.error.URLError as exc:
        raise PocketCastsError(f"could not reach {url}: {exc.reason}") from None


# --- credentials ------------------------------------------------------------


def keychain_get(email: str) -> str | None:
    if not shutil.which("security"):
        return None
    out = sp.run(["security", "find-generic-password", "-s", KEYCHAIN_SERVICE,
                  "-a", email, "-w"], capture_output=True, text=True)
    return out.stdout.strip() or None if out.returncode == 0 else None


def keychain_set(email: str, password: str) -> bool:
    if not shutil.which("security"):
        return False
    out = sp.run(["security", "add-generic-password", "-U", "-s", KEYCHAIN_SERVICE,
                  "-a", email, "-w", password], capture_output=True, text=True)
    return out.returncode == 0


def resolve_password(email: str, allow_prompt: bool = True) -> str:
    for source in (os.environ.get("POCKETCASTS_PASSWORD"), keychain_get(email)):
        if source:
            return source
    if not allow_prompt or not sys.stdin.isatty():
        raise PocketCastsError(
            "no password available. Set POCKETCASTS_PASSWORD, or run "
            "'python3 pocketcasts.py login' once to save it to the keychain."
        )
    return getpass.getpass(f"Pocket Casts password for {email}: ")


# --- auth -------------------------------------------------------------------


def token_path() -> Path:
    return STATE_DIR / "pocketcasts-token.json"


def cached_token(email: str) -> str | None:
    path = token_path()
    if not path.exists():
        return None
    try:
        blob = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    if blob.get("email") != email:
        return None
    # Tokens are not long-lived; a stale one is caught by a 401 and refreshed.
    if time.time() - blob.get("obtained_at", 0) > 25 * 24 * 3600:
        return None
    return blob.get("token")


def store_token(email: str, token: str) -> None:
    path = token_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"email": email, "token": token,
                                "obtained_at": time.time()}), encoding="utf-8")
    path.chmod(0o600)


def login(email: str, password: str, scope: str = "mobile") -> str:
    payload = json.dumps({"email": email, "password": password,
                          "scope": scope}).encode("utf-8")
    try:
        _, body = _request(API + "user/login", data=payload,
                           headers={"Content-Type": "application/json"},
                           method="POST", timeout=60)
    except PocketCastsError as exc:
        if "HTTP 401" in str(exc) or "HTTP 403" in str(exc):
            raise PocketCastsError(
                "Pocket Casts rejected those credentials. Note that uploading "
                "Files needs a Plus or Patron account."
            ) from None
        raise
    try:
        blob = json.loads(body)
    except json.JSONDecodeError:
        raise PocketCastsError("login response was not JSON") from None
    token = blob.get("token") or blob.get("accessToken")
    if not token:
        raise PocketCastsError(f"no token in login response: {sorted(blob)}")
    store_token(email, token)
    return token


def get_token(email: str, *, force: bool = False) -> str:
    if not force:
        token = cached_token(email)
        if token:
            return token
    return login(email, resolve_password(email))


# --- upload -----------------------------------------------------------------


def probe_duration(path: Path) -> int:
    """Seconds, via ffprobe. Zero is accepted by the server, just less tidy."""
    if not shutil.which("ffprobe"):
        return 0
    out = sp.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                  "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
                 capture_output=True, text=True)
    try:
        return int(float(out.stdout.strip()))
    except (ValueError, TypeError):
        return 0


def content_type_for(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix in CONTENT_TYPES:
        return CONTENT_TYPES[suffix]
    guessed, _ = mimetypes.guess_type(path.name)
    return guessed or "audio/mp3"


def upload_file(path: Path, email: str, *, title: str | None = None,
                duration: int | None = None, api: str | None = None) -> str:
    api = api or API      # resolved per call, so the base URL stays overridable
    path = Path(path)
    if not path.is_file():
        raise PocketCastsError(f"{path} is not a file")

    size = path.stat().st_size
    title = title or path.stem
    content_type = content_type_for(path)
    if duration is None:
        duration = probe_duration(path)
    file_uuid = str(uuidlib.uuid4())

    body = build_upload_request(file_uuid, title, size, content_type, duration)

    def request_slot(token: str):
        return _request(
            api + "files/upload/request", data=body, method="POST",
            headers={"Authorization": f"Bearer {token}",
                     "Content-Type": "application/octet-stream"},
        )

    token = get_token(email)
    try:
        _, response = request_slot(token)
    except PocketCastsError as exc:
        if "HTTP 401" not in str(exc):
            raise
        token = get_token(email, force=True)   # expired token, get a fresh one
        _, response = request_slot(token)

    put_url = parse_upload_response(response)

    with path.open("rb") as fh:
        _request(put_url, data=fh, method="PUT",
                 headers={"Content-Type": content_type,
                          "Content-Length": str(size)}, timeout=3600)
    return file_uuid


# --- cli --------------------------------------------------------------------


def main() -> int:
    ap = argparse.ArgumentParser(prog="pocketcasts",
                                 description="Upload files into Pocket Casts Files.")
    ap.add_argument("action", choices=["login", "upload"])
    ap.add_argument("files", nargs="*", type=Path)
    ap.add_argument("--email", default=os.environ.get("POCKETCASTS_EMAIL"),
                    help="account email (or set POCKETCASTS_EMAIL)")
    args = ap.parse_args()

    if not args.email:
        print("error: pass --email or set POCKETCASTS_EMAIL", file=sys.stderr)
        return 1

    try:
        if args.action == "login":
            password = resolve_password(args.email)
            login(args.email, password)
            if keychain_set(args.email, password):
                print("saved password to the login keychain")
            print(f"logged in as {args.email}; token cached at {token_path()}")
            return 0

        if not args.files:
            print("error: upload needs at least one file", file=sys.stderr)
            return 1
        failed = 0
        for path in args.files:
            mb = path.stat().st_size / 1e6 if path.is_file() else 0
            print(f"uploading {path.name} ({mb:.0f} MB)")
            try:
                upload_file(path, args.email)
                print("   done")
            except PocketCastsError as exc:
                failed += 1
                print(f"   FAILED {exc}", file=sys.stderr)
        return 1 if failed else 0
    except PocketCastsError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
