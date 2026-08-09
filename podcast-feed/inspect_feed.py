#!/usr/bin/env python3
"""Report what media a podcast feed actually carries.

Answers the question "is there video in this feed, or is the video only on
YouTube?" by looking at what the RSS enclosures really are, rather than at
what a directory site claims.

    python3 podcast-feed/inspect_feed.py <feed-url> [<feed-url> ...]
"""

import sys
import urllib.request
import xml.etree.ElementTree as ET
from collections import Counter

ITUNES_NS = "http://www.itunes.com/dtds/podcast-1.0.dtd"
PODCAST_NS = "https://podcastindex.org/namespace/1.0"
MEDIA_NS = "http://search.yahoo.com/mrss/"
UA = "chj-podcast-feed/1.0 (feed inspector)"

DEFAULT_FEEDS = ["https://anchor.fm/s/1035b1568/podcast/rss"]


def inspect(url: str) -> None:
    print(f"\n{'=' * 70}\n{url}\n{'=' * 70}")
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=45) as resp:
        print(f"HTTP {resp.status}  content-type: {resp.headers.get('Content-Type')}")
        raw = resp.read()
    print(f"{len(raw)} bytes")

    root = ET.fromstring(raw)
    channel = root.find("channel")
    if channel is None:
        print("no <channel>")
        return

    items = channel.findall("item")
    print(f"channel title: {channel.findtext('title')!r}")
    print(f"items: {len(items)}")

    types = Counter()
    exts = Counter()
    for item in items:
        for enc in item.findall("enclosure"):
            types[enc.get("type", "(none)")] += 1
            exts[enc.get("url", "").split("?")[0].rsplit(".", 1)[-1][:6].lower()] += 1

    print(f"\nenclosure types: {dict(types)}")
    print(f"url extensions : {dict(exts)}")

    video = [t for t in types if t.lower().startswith("video/")]
    print(f"\nVIDEO ENCLOSURES: {'YES -> ' + str(video) if video else 'NO (audio only)'}")

    # Podcasting 2.0 lets a feed offer a video alternative alongside the audio.
    alts = channel.findall(f".//{{{PODCAST_NS}}}alternateEnclosure")
    print(f"podcast:alternateEnclosure elements: {len(alts)}")
    for a in alts[:5]:
        print(f"  type={a.get('type')} title={a.get('title')}")

    media = channel.findall(f".//{{{MEDIA_NS}}}content")
    vid_media = [m for m in media if (m.get("type") or "").startswith("video/")]
    print(f"media:content elements: {len(media)} (video: {len(vid_media)})")

    if items:
        first = items[0]
        print(f"\nmost recent item: {first.findtext('title')!r}")
        for enc in first.findall("enclosure"):
            print(f"  enclosure type={enc.get('type')} len={enc.get('length')}")
            print(f"  url={enc.get('url')[:120]}")
        link = first.findtext("link")
        if link:
            print(f"  link={link[:120]}")


if __name__ == "__main__":
    for feed in (sys.argv[1:] or DEFAULT_FEEDS):
        try:
            inspect(feed)
        except Exception as exc:  # diagnostic tool: report and keep going
            print(f"FAILED {feed}: {type(exc).__name__}: {exc}")
