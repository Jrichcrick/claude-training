# ytqueue

*How I AI* publishes to YouTube, and a screen-share show doesn't survive the
trip to audio — the demo *is* the episode. So this pulls new episodes down as
`2026-08-18 - Episode title.mp4` files and hands them to you ready to upload
into **Pocket Casts Files**, where they sit in Up Next next to your real
subscriptions.

It's not specific to that one show. Any YouTube channel your podcast app can't
subscribe to can go in the config.

Discovery uses YouTube's public per-channel RSS feeds — no API key, no login.
Downloading is delegated to `yt-dlp`. Everything fetched is recorded in a
yt-dlp-compatible archive file, so nothing is ever downloaded twice.

## Setup

Needs Python 3.11+ (for `tomllib`).

```bash
brew install yt-dlp ffmpeg        # ffmpeg is optional but gives better quality
cd tools/ytqueue
python3 ytqueue.py --init         # writes feeds.toml, pre-filled with How I AI
```

Then:

```bash
python3 ytqueue.py --catch-up     # mark the back catalogue as seen
python3 ytqueue.py --dry-run      # see what's new
python3 ytqueue.py --reveal       # download it and open the folder
```

`--catch-up` on the first run matters: without it, the first real run fetches
every episode inside your `max_age_days` window at once.

## Uploading automatically

`--upload` pushes each new episode straight into Pocket Casts Files, so a run
ends with the episode already on your phone:

```bash
export POCKETCASTS_EMAIL="you@example.com"
python3 pocketcasts.py login      # prompts once, saves to the login keychain
python3 ytqueue.py --upload
```

Set `upload = true` under `[settings]` to make that the default. The password
is read from `POCKETCASTS_PASSWORD`, then the macOS login keychain, then a
prompt — it is never written to the config file. The bearer token is cached
`0600` in the state dir and silently refreshed when it expires.

If an upload fails the file stays on disk and the run prints a ready-to-paste
retry:

```bash
python3 pocketcasts.py upload '~/Podcasts/YouTube/2026-08-18 - Episode.mp4'
```

### How it works, and what that means for you

Pocket Casts has no published API. The endpoints and the protobuf field
numbers came from Pocket Casts' own open-source iOS client: log in for a
bearer token, register the file to get a presigned URL, PUT the bytes there.

Two things follow from that. It needs **Plus or Patron** — Files is a paid
feature. And it can break without warning, since nothing obliges them to keep
an undocumented interface stable. When it breaks it will be an HTTP error from
one of those two calls, and `--reveal` plus a manual drag is always the
fallback.

`test_pocketcasts.py` covers the wire format and the whole upload flow against
a local mock, so you can tell a protocol change from a bug here:

```bash
python3 test_pocketcasts.py
```

## Uploading by hand

Pocket Casts calls user uploads **Files**, and it's a Plus/Patron feature.

1. Go to [play.pocketcasts.com](https://play.pocketcasts.com) → **Files** →
   **Upload**, and drop the `.mp4` files in. (The mobile app can upload too,
   but the web player is far less painful for a batch.)
2. They sync to your phone and show up in Files with a generic icon.
3. Add them to **Up Next** and they queue alongside everything else.

The `YYYY-MM-DD - ` prefix keeps them in episode order in any view that sorts
by name.

If Pocket Casts rejects a file as too large, or your cloud storage fills up,
drop `quality` to `480p` — or to `audio`, if you're listening to that one
rather than watching it.

## Config

Everything in `[settings]` is a default; most keys can be repeated inside a
`[[channel]]` block to override them for that show.

| Key | Default | What it does |
| --- | --- | --- |
| `output_dir` | `~/Podcasts/YouTube` | Where files land |
| `archive` | `~/.local/state/ytqueue/downloaded.txt` | What's already been fetched |
| `max_age_days` | `14` | Ignore anything published before this |
| `min_duration_minutes` | `3` | Drops Shorts and clip posts |
| `max_duration_minutes` | `180` | Drops multi-hour streams |
| `quality` | `720p` | `1080p`, `720p`, `480p`, or `audio` (m4a) |
| `limit_per_channel` | `5` | Most recent N feed items considered per run |
| `embed_thumbnail` | `false` | Cover art in the file (needs ffmpeg) |
| `upload` | `false` | Upload to Pocket Casts without needing `--upload` |
| `email` | — | Pocket Casts account email (or `POCKETCASTS_EMAIL`) |

`720p` is the default because it's about the floor for reading text in a
screen share, and going higher just costs upload time and storage.

## Flags

```
--upload           push new episodes into Pocket Casts Files
--dry-run          list what's new, download nothing
--catch-up         mark everything current as seen, download nothing
--reveal           open the output folder when the run finishes
--only NAME        just the channels whose name contains NAME
--since DAYS       override max_age_days for this run
--limit N          override limit_per_channel for this run
--out DIR          override output_dir for this run
--config PATH      use a different config file (default: feeds.toml)
```

Exit status is 1 if any channel or download failed, so it's safe to wire into
something that reports failures.

## Running it on a schedule

*How I AI* posts weekly, so a daily check is plenty. Via `cron` (`crontab -e`):

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
- Episodes rejected by the duration/live filters are written to the archive so
  they aren't re-checked on every run.
- `--upload` drives an undocumented Pocket Casts endpoint (see above). Without
  it, the tool just leaves files in a folder for you to drag in, which nothing
  can break.
