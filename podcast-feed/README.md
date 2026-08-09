# Claire Hughes Johnson podcast feed

A personal podcast RSS feed containing every episode featuring Claire Hughes
Johnson, wherever it was published. Subscribe once in Pocket Casts and new
appearances show up on their own.

## Subscribe

In Pocket Casts: **Profile → Settings → Add URL**, then paste:

```
https://raw.githubusercontent.com/Jrichcrick/claude-training/refs/heads/claude/podcast-video-pocket-casts-tuc1dx/docs/feed.xml
```

Items carry real `<enclosure>` audio URLs pointing at each show's own CDN, so
episodes stream and download normally. Nothing is re-hosted here — this feed is
a pointer list, not a copy of anyone's audio.

## How it finds episodes

Two passes run on every build, and their results are merged:

| Pass | Good at | Weak at |
| --- | --- | --- |
| iTunes Search API episode search | Finding her on shows she has never been on before | Incomplete index, lags a few days |
| Direct scan of `watch_feeds` in `seeds.json` | Immediate and authoritative for shows she recurs on | Only sees shows already on the list |

### Appearance vs. mention

Matching on her name alone does not work. `Scaling People` gets recommended
constantly, so a name-only filter fills the feed with book-roundup episodes she
has nothing to do with. An episode is only accepted on one of three signals,
recorded as `evidence` on each stored entry:

| Evidence | Meaning |
| --- | --- |
| `person-tag` | A `<podcast:person>` credit names her outright |
| `title` | Her name is in the episode title |
| `description-cue` | Her name appears near guest wording — "joins", "sits down with", "speaks with" |

A description that names her with no such wording nearby is treated as a
citation, not an appearance, and skipped. Anything accepted is written to
`known_episodes.json` and never removed, so an episode that later drops out of
a search index stays subscribed.

If a real appearance ever gets filtered out, add its show to `watch_feeds` — or
widen `GUEST_CUES` in `build_feed.py`.

## Adding a show to watch

Append it to `watch_feeds` in `seeds.json`:

```json
{ "show": "Some Podcast", "url": "https://example.com/feed.xml" }
```

Use the show's real RSS URL, not its Apple or Spotify page. The next run picks
up every past episode of that show mentioning her, not just future ones.

## Running it by hand

```bash
python3 podcast-feed/build_feed.py
```

Standard library only, no dependencies. It rewrites `podcast-feed/known_episodes.json`
and `docs/feed.xml`, and prints anything new it found.

## Scheduling caveat

`.github/workflows/chj-podcast-feed.yml` is set to run weekly, but **GitHub only
honours `schedule:` on a repository's default branch.** While this lives on a
feature branch the weekly run will not fire; it rebuilds on push instead. Merge
to the default branch to turn the weekly schedule on.

## Cover art

The feed ships without channel artwork rather than pointing at a placeholder
that 404s. To add some, host a square PNG (1400×1400 or larger) anywhere public
and set `FEED_IMAGE` at the top of `build_feed.py` to its URL.
