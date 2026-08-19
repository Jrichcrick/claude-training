#!/usr/bin/env python3
"""
Checks for the hand-rolled protobuf encoding and the Pocket Casts upload flow.

The upload protocol is undocumented, so the byte-level assertions below are
hand-computed from the protobuf wire format spec rather than from our own
encoder - if someone "fixes" the encoder wrongly, these fail. The flow test
runs against a local mock of the API, so it needs no account and no network.

    python3 test_pocketcasts.py
"""

import http.server
import json
import os
import socketserver
import tempfile
import threading
from pathlib import Path

import pocketcasts as pc


def test_varints():
    assert pc._varint(0) == b"\x00"
    assert pc._varint(127) == b"\x7f"
    assert pc._varint(128) == b"\x80\x01"
    assert pc._varint(300) == b"\xac\x02"


def test_field_encoding():
    # tag byte = (field_number << 3) | wire_type
    assert pc._pb_string(1, "ab") == b"\x0a\x02ab"          # 1<<3|2 = 0x0a
    assert pc._pb_string(4, "video/mp4") == b"\x22\x09video/mp4"
    assert pc._pb_int(3, 300) == b"\x18\xac\x02"            # 3<<3|0 = 0x18
    assert pc._pb_bool(7, False) == b"\x38\x00"             # 7<<3|0 = 0x38
    assert pc._pb_message(6, b"") == b"\x32\x00"            # 6<<3|2 = 0x32


def test_upload_request_shape():
    """Field numbers come from Pocket Casts' own iOS client (files.pb.swift)."""
    body = pc.build_upload_request("u-1", "Ep", 12345, "video/mp4", 1800)
    got = {f: v for f, _, v in pc._pb_fields(body)}
    assert got[1] == b"u-1"          # uuid
    assert got[2] == b"Ep"           # title
    assert got[3] == 12345           # size
    assert got[4] == b"video/mp4"    # contentType
    assert got[5] == 1800            # duration
    assert got[6] == b""             # colour: Int32Value(0)
    assert got[7] == 0               # hasCustomImage


def test_response_parsing():
    blob = pc._pb_string(1, "uuid") + pc._pb_string(2, "https://example/put")
    assert pc.parse_upload_response(blob) == "https://example/put"
    try:
        pc.parse_upload_response(pc._pb_string(1, "uuid-only"))
    except pc.PocketCastsError:
        pass
    else:
        raise AssertionError("a response with no URL should raise")


def test_content_types():
    assert pc.content_type_for(Path("a.mp4")) == "video/mp4"
    assert pc.content_type_for(Path("a.m4a")) == "audio/mp4"
    assert pc.content_type_for(Path("a.mp3")) == "audio/mp3"


class _Mock(http.server.BaseHTTPRequestHandler):
    seen = {}
    port = 0

    def log_message(self, *args):
        pass

    def _body(self):
        return self.rfile.read(int(self.headers.get("Content-Length", 0)))

    def _reply(self, status, payload=b""):
        self.send_response(status)
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_POST(self):
        data = self._body()
        if self.path == "/user/login":
            if json.loads(data).get("password") != "right":
                return self._reply(401, b"nope")
            return self._reply(200, json.dumps({"token": "TOK"}).encode())
        assert self.headers["Authorization"] == "Bearer TOK"
        assert self.headers["Content-Type"] == "application/octet-stream"
        fields = {f: v for f, _, v in pc._pb_fields(data)}
        _Mock.seen["fields"] = fields
        payload = pc._pb_string(1, fields[1].decode())
        payload += pc._pb_string(2, f"http://127.0.0.1:{_Mock.port}/put")
        self._reply(200, payload)

    def do_PUT(self):
        _Mock.seen["bytes"] = self._body()
        _Mock.seen["content_type"] = self.headers.get("Content-Type")
        _Mock.seen["chunked"] = self.headers.get("Transfer-Encoding")
        self._reply(200)


def test_upload_flow():
    with socketserver.TCPServer(("127.0.0.1", 0), _Mock) as srv, \
            tempfile.TemporaryDirectory() as tmp:
        _Mock.port = srv.server_address[1]
        threading.Thread(target=srv.serve_forever, daemon=True).start()

        pc.API = f"http://127.0.0.1:{_Mock.port}/"
        pc.STATE_DIR = Path(tmp) / "state"
        os.environ["POCKETCASTS_PASSWORD"] = "right"

        episode = Path(tmp) / "2026-08-18 - An episode.mp4"
        payload = os.urandom(300_000)
        episode.write_bytes(payload)

        pc.upload_file(episode, "me@example.com", duration=1802)
        fields = _Mock.seen["fields"]
        assert fields[2].decode() == "2026-08-18 - An episode"
        assert fields[3] == len(payload)
        assert fields[4].decode() == "video/mp4"
        assert fields[5] == 1802
        assert _Mock.seen["bytes"] == payload, "uploaded bytes differ from the file"
        assert _Mock.seen["content_type"] == "video/mp4"
        # A presigned S3 PUT rejects chunked transfer encoding.
        assert _Mock.seen["chunked"] is None

        token_file = pc.token_path()
        assert oct(token_file.stat().st_mode)[-3:] == "600"

        # An expired token should trigger one silent re-login, then succeed.
        pc.store_token("me@example.com", "STALE")
        attempts = []
        original = pc._request

        def flaky(url, **kwargs):
            if url.endswith("files/upload/request"):
                attempts.append(kwargs["headers"]["Authorization"])
                if kwargs["headers"]["Authorization"] == "Bearer STALE":
                    raise pc.PocketCastsError("HTTP 401 from x\n  expired")
            return original(url, **kwargs)

        pc._request = flaky
        try:
            pc.upload_file(episode, "me@example.com", duration=1)
        finally:
            pc._request = original
        assert attempts == ["Bearer STALE", "Bearer TOK"], attempts

        # Bad credentials should explain the Plus requirement.
        os.environ["POCKETCASTS_PASSWORD"] = "wrong"
        pc.token_path().unlink()
        try:
            pc.upload_file(episode, "me@example.com")
        except pc.PocketCastsError as exc:
            assert "Plus or Patron" in str(exc), exc
        else:
            raise AssertionError("bad credentials should raise")

        srv.shutdown()


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for test in tests:
        test()
        print(f"ok  {test.__name__}")
    print(f"\n{len(tests)} passed")
