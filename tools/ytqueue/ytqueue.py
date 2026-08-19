#!/usr/bin/env python3
"""
ytqueue - pull new episodes of How I AI (and any other YouTube channel that
never made it into your podcast app) and save them as "YYYY-MM-DD - Title.mp4"
files, ready to upload to Pocket Casts Files.

Discovery uses YouTube's public per-channel RSS feeds, so there is no API key
and no scraping of the channel page (except once, to turn an @handle into a
channel id). Downloading is delegated to yt-dlp. Everything already fetched is
recorded in a yt-dlp-compatible archive file, so nothing is downloaded twice.

    python3 ytqueue.py --init          # write a starter feeds.toml
    python3 ytqueue.py --dry-run       # show what's new, download nothing
    python3 ytqueue.py --catch-up      # mark everything current as seen
    python3 ytqueue.py                 # download the new stuff
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from xml.etree import ElementTree

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python < 3.11
    sys.exit("ytqueue needs Python 3.11 or newer (it reads TOML with tomllib).")

ATOM = "{http://www.w3.org/2005/Atom}"
YT = "{http://www.youtube.com/xml/schemas/2015}"

UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)

DEFAULTS = {
    "output_dir": "~/Podcasts/YouTube",
    "archive": "~/.local/state/ytqueue/downloaded.txt",
    "max_age_days": 14,
    "min_duration_minutes": 3,
    "max_duration_minutes": 180,
    "quality": "720p",
    "embed_thumbnail": False,
    "limit_per_channel": 5,
}

PER_CHANNEL_OVERRIDES = (
    "max_age_days",
    "min_duration_minutes",
    "max_duration_minutes",
    "quality",
    "limit_per_channel",
    "output_dir",
)

STARTER_CONFIG = '''\
# ytqueue - one [[channel]] block per show you want in your Pocket Casts queue.
# Channel URLs, @handles, /channel/UC... ids and playlist URLs all work.

[settings]
output_dir = "~/Podcasts/YouTube"
max_age_days = 14            # ignore anything published longer ago than this
min_duration_minutes = 3     # drops Shorts
max_duration_minutes = 180
quality = "720p"             # 1080p | 720p | 480p | audio
limit_per_channel = 5        # most recent N feed items considered per run

[[channel]]
name = "How I AI"
url = "https://www.youtube.com/@howiaipodcast"

# Add more the same way. Per-channel overrides go inside the block:
#
# [[channel]]
# name = "Big Technology Podcast"
# url = "https://www.youtube.com/@BigTechnologyPodcast"
# max_age_days = 7
'''


# --- small helpers ----------------------------------------------------------


def die(msg: str) -> "NoReturn":  # noqa: F821
    print(f"error: {msg}", file=sys.stderr)
    raise SystemExit(1)


def expand(path: str) -> Path:
    return Path(path).expanduser()


def fetch(url: str, timeout: int = 30) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


# --- config -----------------------------------------------------------------


def load_config(path: Path) -> tuple[dict, list[dict]]:
    if not path.exists():
        die(f"no config at {path}. Run: python3 {Path(sys.argv[0]).name} --init")
    try:
        raw = tomllib.loads(path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as exc:
        die(f"{path} is not valid TOML: {exc}")

    settings = dict(DEFAULTS)
    settings.update(raw.get("settings", {}))

    channels = raw.get("channel", [])
    if not channels:
        die(f"{path} has no [[channel]] blocks - nothing to check")

    resolved = []
    for i, chan in enumerate(channels, 1):
        if "url" not in chan:
            die(f"channel #{i} in {path} is missing a url")
        merged = dict(settings)
        merged.update({k: v for k, v in chan.items() if k in PER_CHANNEL_OVERRIDES})
        merged["name"] = chan.get("name") or chan["url"]
        merged["url"] = chan["url"]
        resolved.append(merged)
    return settings, resolved


# --- feed discovery ---------------------------------------------------------


def feed_url_for(url: str, cache: dict) -> str:
    """Turn any YouTube channel/playlist URL into its RSS feed URL."""
    if "feeds/videos.xml" in url or url.startswith("file://"):
        return url

    m = re.search(r"youtube\.com/channel/(UC[\w-]{22})", url)
    if m:
        return f"https://www.youtube.com/feeds/videos.xml?channel_id={m.group(1)}"

    m = re.search(r"[?&]list=([\w-]+)", url)
    if m:
        return f"https://www.youtube.com/feeds/videos.xml?playlist_id={m.group(1)}"

    if re.fullmatch(r"UC[\w-]{22}", url):
        return f"https://www.youtube.com/feeds/videos.xml?channel_id={url}"

    # An @handle, /c/name or /user/name: resolve it once, then cache the id.
    if url in cache:
        return f"https://www.youtube.com/feeds/videos.xml?channel_id={cache[url]}"

    page_url = url if url.startswith("http") else f"https://www.youtube.com/{url.lstrip('/')}"
    try:
        html = fetch(page_url).decode("utf-8", "replace")
    except (urllib.error.URLError, OSError) as exc:
        die(f"could not open {page_url} to find its channel id: {exc}")

    m = re.search(r'"channelId":"(UC[\w-]{22})"', html) or re.search(
        r'youtube\.com/channel/(UC[\w-]{22})', html
    )
    if not m:
        die(f"could not find a channel id on {page_url} - try the /channel/UC... URL instead")

    cache[url] = m.group(1)
    return f"https://www.youtube.com/feeds/videos.xml?channel_id={m.group(1)}"


def parse_feed(data: bytes) -> list[dict]:
    try:
        root = ElementTree.fromstring(data)
    except ElementTree.ParseError as exc:
        die(f"feed is not valid XML: {exc}")

    items = []
    for entry in root.findall(f"{ATOM}entry"):
        vid = entry.findtext(f"{YT}videoId")
        title = (entry.findtext(f"{ATOM}title") or "").strip()
        published = entry.findtext(f"{ATOM}published")
        if not (vid and published):
            continue
        try:
            when = datetime.fromisoformat(published)
        except ValueError:
            continue
        if when.tzinfo is None:
            when = when.replace(tzinfo=timezone.utc)
        items.append({"id": vid, "title": title or vid, "published": when})
    items.sort(key=lambda i: i["published"], reverse=True)
    return items


# --- archive ----------------------------------------------------------------


def read_archive(path: Path) -> set[str]:
    if not path.exists():
        return set()
    seen = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        parts = line.split()
        if len(parts) == 2:
            seen.add(parts[1])
    return seen


def mark_seen(path: Path, video_id: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(f"youtube {video_id}\n")


# --- downloading ------------------------------------------------------------


def format_args(quality: str, have_ffmpeg: bool) -> list[str]:
    if quality == "audio":
        return ["-f", "ba[ext=m4a]/ba"]
    heights = {"1080p": 1080, "720p": 720, "480p": 480}
    if quality not in heights:
        die(f"quality must be one of 1080p, 720p, 480p, audio (got {quality!r})")
    h = heights[quality]
    if have_ffmpeg:
        fmt = f"bv*[height<={h}][ext=mp4]+ba[ext=m4a]/b[height<={h}][ext=mp4]/b[ext=mp4]/b"
        return ["-f", fmt, "--merge-output-format", "mp4"]
    # Without ffmpeg nothing can be muxed, so take the best pre-muxed file.
    return ["-f", f"b[height<={h}][ext=mp4]/b[ext=mp4]/b"]


def download(item: dict, chan: dict, archive: Path, have_ffmpeg: bool) -> tuple[str, str]:
    """Returns (status, detail). status is one of: ok, filtered, failed."""
    out_dir = expand(chan["output_dir"])
    out_dir.mkdir(parents=True, exist_ok=True)
    prefix = item["published"].astimezone(timezone.utc).strftime("%Y-%m-%d")

    filters = (
        f"duration >= {int(chan['min_duration_minutes']) * 60} & "
        f"duration <= {int(chan['max_duration_minutes']) * 60} & "
        "!is_live & live_status != is_upcoming"
    )

    with tempfile.NamedTemporaryFile("w+", suffix=".txt", delete=False) as tmp:
        printed = Path(tmp.name)

    cmd = [
        "yt-dlp",
        "--no-playlist",
        "--newline",
        "--no-progress",
        "--paths", str(out_dir),
        "-o", f"{prefix} - %(title)s.%(ext)s",
        "--trim-filenames", "150",
        "--download-archive", str(archive),
        "--match-filters", filters,
        "--embed-metadata",
        "--print-to-file", "after_move:filepath", str(printed),
        *format_args(chan["quality"], have_ffmpeg),
    ]
    if chan.get("embed_thumbnail"):
        cmd.append("--embed-thumbnail")
    cmd.append(f"https://www.youtube.com/watch?v={item['id']}")

    proc = subprocess.run(cmd, capture_output=True, text=True)
    output = proc.stdout + proc.stderr
    written = printed.read_text(encoding="utf-8").strip()
    printed.unlink(missing_ok=True)

    if "does not pass filter" in output:
        # yt-dlp does not archive filter rejections, so record it here and
        # never look at this video again.
        mark_seen(archive, item["id"])
        return "filtered", "outside the duration/live filters"

    if proc.returncode != 0:
        detail = next(
            (l for l in reversed(output.splitlines()) if l.strip().startswith("ERROR")),
            f"yt-dlp exited {proc.returncode}",
        )
        return "failed", detail.strip()

    return "ok", (written.splitlines()[-1] if written else f"{prefix} - {item['title']}")


# --- main -------------------------------------------------------------------


def main() -> int:
    ap = argparse.ArgumentParser(
        prog="ytqueue",
        description="Save new videos from YouTube channels as dated files for your podcast app.",
    )
    ap.add_argument("-c", "--config", default="feeds.toml", help="config file (default: feeds.toml)")
    ap.add_argument("--init", action="store_true", help="write a starter config and exit")
    ap.add_argument("-n", "--dry-run", action="store_true", help="list what is new, download nothing")
    ap.add_argument("--catch-up", action="store_true", help="mark everything current as seen, download nothing")
    ap.add_argument("--only", metavar="NAME", help="only check channels whose name contains NAME")
    ap.add_argument("--since", type=int, metavar="DAYS", help="override max_age_days")
    ap.add_argument("--limit", type=int, metavar="N", help="override limit_per_channel")
    ap.add_argument("-o", "--out", metavar="DIR", help="override output_dir")
    ap.add_argument("--reveal", action="store_true",
                    help="open the output folder afterwards, to drag files into Pocket Casts")
    args = ap.parse_args()

    config_path = Path(args.config)
    if args.init:
        if config_path.exists():
            die(f"{config_path} already exists - not overwriting it")
        config_path.write_text(STARTER_CONFIG, encoding="utf-8")
        print(f"wrote {config_path} - edit it, then run: python3 {Path(sys.argv[0]).name} --dry-run")
        return 0

    settings, channels = load_config(config_path)

    for chan in channels:
        if args.since is not None:
            chan["max_age_days"] = args.since
        if args.limit is not None:
            chan["limit_per_channel"] = args.limit
        if args.out:
            chan["output_dir"] = args.out
    if args.only:
        needle = args.only.lower()
        channels = [c for c in channels if needle in c["name"].lower()]
        if not channels:
            die(f"no channel name contains {args.only!r}")

    archive = expand(settings["archive"])
    seen = read_archive(archive)

    working = not (args.dry_run or args.catch_up)
    have_ffmpeg = shutil.which("ffmpeg") is not None
    if working:
        if not shutil.which("yt-dlp"):
            die("yt-dlp is not installed. Try: brew install yt-dlp  (or: pipx install yt-dlp)")
        if not have_ffmpeg:
            print("note: ffmpeg not found - falling back to single-file formats "
                  "(lower quality ceiling). brew install ffmpeg\n")

    cache_path = archive.parent / "handles.json"
    cache = {}
    if cache_path.exists():
        try:
            cache = json.loads(cache_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            cache = {}
    cache_before = dict(cache)

    now = datetime.now(timezone.utc)
    downloaded = filtered = failed = queued = 0

    for chan in channels:
        print(f"== {chan['name']}")
        feed = feed_url_for(chan["url"], cache)
        try:
            items = parse_feed(fetch(feed))
        except (urllib.error.URLError, OSError) as exc:
            print(f"   could not read feed: {exc}\n")
            failed += 1
            continue

        cutoff = now - timedelta(days=int(chan["max_age_days"]))
        fresh = [
            i for i in items[: int(chan["limit_per_channel"])]
            if i["published"] >= cutoff and i["id"] not in seen
        ]
        if not fresh:
            print("   nothing new\n")
            continue

        for item in fresh:
            stamp = item["published"].astimezone(timezone.utc).strftime("%Y-%m-%d")
            label = f"{stamp} - {item['title']}"
            if args.catch_up:
                mark_seen(archive, item["id"])
                seen.add(item["id"])
                print(f"   marked seen  {label}")
                queued += 1
                continue
            if args.dry_run:
                print(f"   would fetch  {label}")
                queued += 1
                continue

            print(f"   fetching     {label}")
            status, detail = download(item, chan, archive, have_ffmpeg)
            seen.add(item["id"])
            if status == "ok":
                downloaded += 1
                print(f"   saved        {detail}")
            elif status == "filtered":
                filtered += 1
                print(f"   skipped      {detail}")
            else:
                failed += 1
                print(f"   FAILED       {detail}")
        print()

    if cache != cache_before:
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_text(json.dumps(cache, indent=2), encoding="utf-8")

    if args.dry_run:
        print(f"{queued} new item(s). Drop --dry-run to download them.")
    elif args.catch_up:
        print(f"{queued} item(s) marked as seen. Future runs only fetch what lands next.")
    else:
        parts = [f"{downloaded} downloaded"]
        if filtered:
            parts.append(f"{filtered} skipped by filter")
        if failed:
            parts.append(f"{failed} failed")
        print(", ".join(parts))
        if downloaded:
            out = expand(settings["output_dir"]).resolve()
            print(f"files are in {out}")
            print("upload them at play.pocketcasts.com -> Files -> Upload")
            if args.reveal:
                opener = next((o for o in ("open", "xdg-open") if shutil.which(o)), None)
                if opener:
                    subprocess.run([opener, str(out)], check=False)

    return 1 if failed else 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("\ninterrupted", file=sys.stderr)
        raise SystemExit(130)
