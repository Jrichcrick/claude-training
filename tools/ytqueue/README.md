# ytqueue

Pulls new videos from the YouTube channels you follow and saves them as
`2026-08-18 - Video title.mp4` files, ready to sideload into a podcast app
(Overcast uploads, Apple Podcasts, Plex, whatever) so they land in Up Next
alongside your real podcasts.

Discovery uses YouTube's public per-channel RSS feeds — no API key, no login.
Downloading is delegated to `yt-dlp`. Everything fetched is recorded in a
yt-dlp-compatible archive file, so nothing is ever downloaded twice.

## Setup

Needs Python 3.11+ (for `tomllib`).

```bash
brew install yt-dlp ffmpeg        # ffmpeg is optional but gives better quality
cd tools/ytqueue
python3 ytqueue.py --init         # writes feeds.toml
```

Edit `feeds.toml` and put your channels in it. Channel URLs, `@handles`,
`/channel/UC...` ids, bare channel ids and playlist URLs all work.

Then:

```bash
python3 ytqueue.py --catch-up     # mark today's back catalogue as seen
python3 ytqueue.py --dry-run      # see what's new
python3 ytqueue.py                # download it
```

`--catch-up` on the first run matters: without it, the first real run fetches
every video inside your `max_age_days` window for every channel at once.

## Config

Everything in `[settings]` is a default; anything in `PER_CHANNEL_OVERRIDES`
can be repeated inside a `[[channel]]` block to override it there.

| Key | Default | What it does |
| --- | --- | --- |
| `output_dir` | `~/Podcasts/YouTube` | Where files land |
| `archive` | `~/.local/state/ytqueue/downloaded.txt` | What's already been fetched |
| `max_age_days` | `14` | Ignore anything published before this |
| `min_duration_minutes` | `3` | Drops Shorts |
| `max_duration_minutes` | `180` | Drops multi-hour streams |
| `quality` | `720p` | `1080p`, `720p`, `480p`, or `audio` (m4a) |
| `limit_per_channel` | `5` | Most recent N feed items considered per run |
| `embed_thumbnail` | `false` | Cover art in the file (needs ffmpeg) |

Talking-head video is not worth 1080p if you're mostly listening — `720p` or
`audio` keeps files small enough to sync over cellular.

## Flags

```
--dry-run          list what's new, download nothing
--catch-up         mark everything current as seen, download nothing
--only NAME        just the channels whose name contains NAME
--since DAYS       override max_age_days for this run
--limit N          override limit_per_channel for this run
--out DIR          override output_dir for this run
--config PATH      use a different config file (default: feeds.toml)
```

Exit status is 1 if any channel or download failed, so it's safe to wire into
something that reports failures.

## Getting the files into your podcast app

- **Overcast** (premium): overcast.fm → Uploads → drop the files in. They show
  up in Up Next as generic-icon items with the date prefix as the title.
- **Apple Podcasts / Music**: drag the `.mp4` files into the app; they sync as
  library items.
- **Plex / Jellyfin**: point a library at `output_dir` and let it scan.

The `YYYY-MM-DD - ` prefix is there so the files sort chronologically in any
app that sorts by filename.

## Running it on a schedule

macOS, via `cron` (`crontab -e`) — every morning at 7:

```
0 7 * * * cd ~/path/to/tools/ytqueue && /usr/bin/python3 ytqueue.py >> ~/.local/state/ytqueue/log.txt 2>&1
```

Check `log.txt` occasionally: YouTube changes things, and a stale `yt-dlp` is
the usual cause of sudden failures (`brew upgrade yt-dlp`).

## Notes

- `feeds.toml` and the download state are gitignored — the channel list is
  yours, not the repo's. `feeds.example.toml` is the shared starting point.
- Without `ffmpeg`, the script falls back to pre-muxed single-file formats,
  which caps quality at whatever YouTube offers as one file (usually 720p).
- Videos rejected by the duration/live filters are written to the archive so
  they aren't re-checked on every run.
- This is for personal listening to channels you already follow. It's the same
  thing your podcast app does, aimed at feeds that don't publish audio.
