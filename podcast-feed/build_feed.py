#!/usr/bin/env python3
"""Build a personal podcast RSS feed of every Claire Hughes Johnson appearance.

Two discovery paths run every build:

  1. iTunes Search API episode search, which finds her on shows she has never
     been on before but whose episode index is incomplete and lags by days.
  2. A direct scan of the RSS feeds in seeds.json, which is authoritative and
     immediate for the shows she actually recurs on.

Whatever either path finds is merged into known_episodes.json and never
removed, so an episode that later falls out of a search index stays in the
feed. Output is docs/feed.xml: RSS 2.0 with real <enclosure> audio URLs, so
Pocket Casts can play episodes directly rather than just linking out.

Standard library only -- no pip install in CI.
"""

from __future__ import annotations

import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import format_datetime, parsedate_to_datetime
from pathlib import Path
from xml.sax.saxutils import escape

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
SEEDS_PATH = HERE / "seeds.json"
STORE_PATH = HERE / "known_episodes.json"
OUTPUT_PATH = REPO / "docs" / "feed.xml"

FEED_TITLE = "Claire Hughes Johnson — Every Appearance"
FEED_LINK = "https://github.com/Jrichcrick/claude-training"
FEED_DESCRIPTION = (
    "An automatically maintained feed of every podcast episode featuring "
    "Claire Hughes Johnson, former COO of Stripe and author of Scaling People. "
    "Episodes are collected from across the podcast ecosystem and updated weekly."
)
FEED_AUTHOR = "Claire Hughes Johnson (feed compiled automatically)"
# Where this file is actually served from. Used for atom:link rel="self", which
# podcast clients rely on to re-resolve the feed after a redirect.
FEED_SELF_URL = (
    "https://raw.githubusercontent.com/Jrichcrick/claude-training/"
    "refs/heads/claude/podcast-video-pocket-casts-tuc1dx/docs/feed.xml"
)
# Channel artwork. Left empty by default rather than pointing at a file that
# does not exist -- a 404 here shows as a broken tile in the podcast client.
# Drop a square PNG somewhere public and put its URL here to set cover art.
FEED_IMAGE = ""

USER_AGENT = "chj-podcast-feed/1.0 (+https://github.com/Jrichcrick/claude-training)"
TIMEOUT = 30

ITUNES_NS = "http://www.itunes.com/dtds/podcast-1.0.dtd"
ATOM_NS = "http://www.w3.org/2005/Atom"
PODCAST_NS = "https://podcastindex.org/namespace/1.0"


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------

def log(msg: str) -> None:
    print(msg, flush=True)


def normalize(text: str | None) -> str:
    """Lowercase and collapse whitespace so name matching survives line breaks."""
    if not text:
        return ""
    return re.sub(r"\s+", " ", text).strip().lower()


def strip_html(text: str | None) -> str:
    if not text:
        return ""
    text = re.sub(r"<br\s*/?>", " ", text, flags=re.I)
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"&nbsp;?", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def clean_title(text: str | None) -> str:
    """Feeds routinely wrap titles across lines and pad them with indentation.
    Left alone that whitespace survives into our <title> and renders as a
    ragged mess in the podcast client, so flatten it on the way in."""
    return re.sub(r"\s+", " ", strip_html(text)).strip()


def fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        return resp.read()


# Words that indicate the named person is *on* the episode, as opposed to
# being cited in it. Checked in a window around the name.
GUEST_CUES = (
    "joins", "joined", "join us", "my guest", "our guest", "guest", "guests",
    "sits down with", "sat down with", "in conversation with", "conversation with",
    "talks to", "talks with", "speaks to", "speaks with", "spoke with", "spoke to",
    "interview with", "interviews", "interviewed", "welcome", "welcomes",
    "featuring", "features", "chats with", "returns to", "back on the show",
    "is the", "shares", "explains", "discusses", "tells",
)

# The window is a rough proxy, so require a reasonably tight neighbourhood.
CUE_WINDOW = 140


def find_name_hits(aliases: list[str], text: str) -> list[int]:
    hits = []
    for alias in aliases:
        needle = normalize(alias)
        start = 0
        while (idx := text.find(needle, start)) != -1:
            hits.append(idx)
            start = idx + len(needle)
    return hits


def appearance_evidence(
    aliases: list[str],
    title: str | None,
    description: str | None,
    people: list[str] | None = None,
) -> str | None:
    """Decide whether the person is actually *on* this episode.

    A bare name match is not enough. Podcast descriptions are full of book
    recommendations and 'as discussed by' asides, and treating those as
    appearances fills the feed with episodes she has nothing to do with.
    Returns the reason it was accepted, or None to reject.
    """
    # A <podcast:person> tag is an explicit, machine-readable credit.
    for person in people or []:
        if any(normalize(a) == normalize(person) for a in aliases):
            return "person-tag"

    # Her name in the episode title is a near-certain guest credit.
    if find_name_hits(aliases, normalize(strip_html(title))):
        return "title"

    # In the body, only count it when the surrounding words describe a guest.
    body = normalize(strip_html(description))
    for idx in find_name_hits(aliases, body):
        window = body[max(0, idx - CUE_WINDOW): idx + CUE_WINDOW]
        if any(cue in window for cue in GUEST_CUES):
            return "description-cue"

    return None


def parse_date(value: str | None) -> datetime | None:
    """Accept both RFC 2822 (RSS pubDate) and ISO 8601 (iTunes releaseDate)."""
    if not value:
        return None
    value = value.strip()
    try:
        dt = parsedate_to_datetime(value)
        if dt is not None:
            return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except (TypeError, ValueError, IndexError):
        pass
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def episode_key(show: str, title: str) -> str:
    """Stable identity for an episode across both discovery paths.

    Keyed on the title alone, not show+title: the same episode arrives with
    different show labels depending on the source (iTunes reports "Boss Class
    from The Economist", our seed list calls it "Boss Class (The Economist)"),
    and including the show name lets that one episode into the feed twice.
    Short titles keep the show name because "Episode 20" is not unique.
    """
    slug = re.sub(r"[^a-z0-9]+", "", normalize(title))
    return slug if len(slug) >= 20 else f"{normalize(show)}|{slug}"


# --------------------------------------------------------------------------
# discovery: iTunes Search API
# --------------------------------------------------------------------------

def search_itunes(term: str, aliases: list[str]) -> list[dict]:
    params = urllib.parse.urlencode(
        {"term": term, "media": "podcast", "entity": "podcastEpisode", "limit": 200}
    )
    url = f"https://itunes.apple.com/search?{params}"
    try:
        payload = json.loads(fetch(url).decode("utf-8", "replace"))
    except (urllib.error.URLError, json.JSONDecodeError, TimeoutError) as exc:
        log(f"  ! iTunes search failed for {term!r}: {exc}")
        return []

    found = []
    for r in payload.get("results", []):
        title = r.get("trackName")
        show = r.get("collectionName")
        if not title or not show:
            continue
        # The search index matches loosely, so confirm she is actually on it.
        evidence = appearance_evidence(
            aliases, title, r.get("description") or r.get("shortDescription")
        )
        if not evidence:
            continue
        found.append(
            {
                "show": clean_title(show),
                "title": clean_title(title),
                "evidence": evidence,
                "description": strip_html(r.get("description") or r.get("shortDescription")),
                "published": (parse_date(r.get("releaseDate")) or datetime.now(timezone.utc)).isoformat(),
                "audio_url": r.get("episodeUrl") or "",
                "audio_type": "audio/mpeg",
                "audio_length": "0",
                "page_url": r.get("trackViewUrl") or "",
                "duration_ms": r.get("trackTimeMillis") or 0,
                "artwork": r.get("artworkUrl600") or r.get("artworkUrl160") or "",
                "source": "itunes",
            }
        )
    log(f"  iTunes {term!r}: {len(found)} match(es) out of {payload.get('resultCount', 0)} result(s)")
    return found


# --------------------------------------------------------------------------
# discovery: direct RSS scan
# --------------------------------------------------------------------------

def scan_feed(show: str, url: str, aliases: list[str]) -> list[dict]:
    try:
        root = ET.fromstring(fetch(url))
    except (urllib.error.URLError, ET.ParseError, TimeoutError) as exc:
        log(f"  ! feed scan failed for {show}: {exc}")
        return []

    channel = root.find("channel")
    if channel is None:
        log(f"  ! {show}: no <channel> element")
        return []

    channel_art = ""
    image = channel.find("image/url")
    if image is not None and image.text:
        channel_art = image.text.strip()

    found = []
    for item in channel.findall("item"):
        title = (item.findtext("title") or "").strip()
        if not title:
            continue
        summary = item.findtext("description") or ""
        subtitle = item.findtext(f"{{{ITUNES_NS}}}subtitle") or ""
        itunes_summary = item.findtext(f"{{{ITUNES_NS}}}summary") or ""
        people = [
            (el.text or "").strip()
            for el in item.findall(f"{{{PODCAST_NS}}}person")
            if (el.get("role") or "guest").lower() in ("guest", "host", "cohost")
        ]
        evidence = appearance_evidence(
            aliases, title, " ".join([summary, itunes_summary, subtitle]), people
        )
        if not evidence:
            continue

        enclosure = item.find("enclosure")
        audio_url = enclosure.get("url", "") if enclosure is not None else ""
        if not audio_url:
            continue  # nothing playable, so nothing worth putting in the feed

        found.append(
            {
                "show": clean_title(show),
                "title": clean_title(title),
                "evidence": evidence,
                "description": strip_html(summary or itunes_summary or subtitle),
                "published": (parse_date(item.findtext("pubDate")) or datetime.now(timezone.utc)).isoformat(),
                "audio_url": audio_url,
                "audio_type": enclosure.get("type", "audio/mpeg"),
                "audio_length": enclosure.get("length", "0"),
                "page_url": (item.findtext("link") or "").strip(),
                "duration_ms": 0,
                "artwork": channel_art,
                "source": "rss",
            }
        )
    log(f"  {show}: {len(found)} match(es)")
    return found


# --------------------------------------------------------------------------
# merge + render
# --------------------------------------------------------------------------

def merge(store: dict, discovered: list[dict]) -> tuple[dict, list[dict]]:
    """Add anything new. An entry that already exists is upgraded only when the
    new copy has an audio URL and the stored one does not."""
    new_entries = []
    for ep in discovered:
        key = episode_key(ep["show"], ep["title"])
        existing = store.get(key)
        if existing is None:
            ep["first_seen"] = datetime.now(timezone.utc).isoformat()
            store[key] = ep
            new_entries.append(ep)
        elif not existing.get("audio_url") and ep.get("audio_url"):
            ep["first_seen"] = existing.get("first_seen", datetime.now(timezone.utc).isoformat())
            store[key] = ep
    return store, new_entries


def duration_hms(ms: int) -> str:
    seconds = int(ms // 1000)
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"


def render(store: dict) -> str:
    episodes = [e for e in store.values() if e.get("audio_url")]
    episodes.sort(key=lambda e: e.get("published", ""), reverse=True)

    now = format_datetime(datetime.now(timezone.utc))
    out = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<rss version="2.0" xmlns:itunes="{ITUNES_NS}" xmlns:atom="{ATOM_NS}">',
        "  <channel>",
        f"    <title>{escape(FEED_TITLE)}</title>",
        f"    <link>{escape(FEED_LINK)}</link>",
        f"    <description>{escape(FEED_DESCRIPTION)}</description>",
        "    <language>en-us</language>",
        f"    <lastBuildDate>{now}</lastBuildDate>",
        f"    <itunes:author>{escape(FEED_AUTHOR)}</itunes:author>",
        "    <itunes:explicit>false</itunes:explicit>",
        '    <itunes:category text="Business"><itunes:category text="Management"/></itunes:category>',
        f'    <atom:link href="{escape(FEED_SELF_URL)}" rel="self" type="application/rss+xml"/>',
    ]
    if FEED_IMAGE:
        out.append(f'    <itunes:image href="{escape(FEED_IMAGE)}"/>')

    for ep in episodes:
        published = parse_date(ep.get("published")) or datetime.now(timezone.utc)
        # Prefix the show name so the source is obvious in the Pocket Casts list.
        title = f"{ep['show']} — {ep['title']}"
        guid = episode_key(ep["show"], ep["title"])
        out += [
            "    <item>",
            f"      <title>{escape(title)}</title>",
            f'      <guid isPermaLink="false">{escape(guid)}</guid>',
            f"      <pubDate>{format_datetime(published)}</pubDate>",
            f"      <description>{escape(ep.get('description') or title)}</description>",
            f"      <itunes:author>{escape(ep['show'])}</itunes:author>",
            f'      <enclosure url="{escape(ep["audio_url"])}" '
            f'type="{escape(ep.get("audio_type") or "audio/mpeg")}" '
            f'length="{escape(str(ep.get("audio_length") or 0))}"/>',
        ]
        if ep.get("page_url"):
            out.append(f"      <link>{escape(ep['page_url'])}</link>")
        if ep.get("duration_ms"):
            out.append(f"      <itunes:duration>{duration_hms(ep['duration_ms'])}</itunes:duration>")
        if ep.get("artwork"):
            out.append(f'      <itunes:image href="{escape(ep["artwork"])}"/>')
        out.append("    </item>")

    out += ["  </channel>", "</rss>", ""]
    return "\n".join(out)


# --------------------------------------------------------------------------

def main() -> int:
    seeds = json.loads(SEEDS_PATH.read_text())
    aliases = seeds["person"]["aliases"]
    store = json.loads(STORE_PATH.read_text()) if STORE_PATH.exists() else {}
    log(f"Loaded {len(store)} previously known episode(s).")

    discovered: list[dict] = []

    log("Searching the iTunes episode index...")
    for term in seeds.get("search_terms", []):
        discovered += search_itunes(term, aliases)

    log("Scanning watched show feeds...")
    for feed in seeds.get("watch_feeds", []):
        discovered += scan_feed(feed["show"], feed["url"], aliases)

    if not discovered and not store:
        log("ERROR: no episodes found and no prior store -- refusing to write an empty feed.")
        return 1

    store, new_entries = merge(store, discovered)

    STORE_PATH.write_text(json.dumps(store, indent=2, sort_keys=True) + "\n")
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(render(store))

    playable = sum(1 for e in store.values() if e.get("audio_url"))
    log(f"\n{len(store)} known episode(s), {playable} with playable audio.")
    if new_entries:
        log(f"{len(new_entries)} new since last run:")
        for ep in new_entries:
            log(f"  + {ep['show']} — {ep['title']}")
    else:
        log("No new episodes this run.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
