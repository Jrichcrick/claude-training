# podcast-insights

Extract implementable tactics from new episodes of **The AI Daily Brief** (NLW) and **How I AI**
(Claire Vo), add them to JR's technique library, and deliver a digest.

Runs nightly at ~7:07pm ET via a Routine. Also runnable by hand: `/podcast-insights`.

Read `podcast-insights/config.json` first — it holds the podcast list, the recipient, the filter
rules, and the audience context. Config wins over anything hardcoded below.

---

## Step 0 — Make sure you have the repo

The Routine fires a fresh session whose primary repo is `nyc-marathon-2026`, not this one. If
`/workspace/claude-training` is not present:

1. `add_repo` with owner `Jrichcrick`, repo `claude-training`, access `push`
2. `git clone --depth 1 https://github.com/jrichcrick/claude-training /workspace/claude-training`
   (generous timeout, one attempt)
3. `git -C /workspace/claude-training checkout claude/podcast-insights-automation-wqfioa || git -C /workspace/claude-training checkout -b claude/podcast-insights-automation-wqfioa`

Always `git pull` the branch before editing so you build on the previous night's ledger.

## Step 1 — Find what's new (from feed-bridge, never from the network)

This sandbox **cannot** reach anchor.fm, itunes.apple.com, aidailybrief.ai, podcasts.apple.com,
or YouTube (403 at the proxy). Do not curl, WebFetch, or WebSearch for episodes. Everything you
need is mirrored into the **feed-bridge** repo, which is checked out next to this one (usually
`/home/user/feed-bridge`; `config.source_repo` has the hint). Read its `README.md` once.

1. Read `feed-bridge/status.json`. If `run_at` is older than `config.source_repo.stale_after_hours`,
   the mirror is stale (Jilly's Mac is probably asleep). Record `"status": "bridge_stale"` in the
   ledger, commit, and make your final message one line saying so. Do not guess from search.
2. For each podcast in `config.podcasts`, read `feed-bridge/<bridge_path>/episodes.json`. Take
   every episode published since `processed.json.last_run_utc` (first run for a new podcast: the
   most recent 3). Drop any whose GUID already appears in `processed.json.episodes`.
3. For each candidate, find its transcript: `feed-bridge/<bridge_path>/transcripts/index.json`
   maps YouTube video id → title/date/file. Match by **date (same day or ±1) and title similarity**,
   not exact title; the video title often differs slightly from the audio title. Read the `.txt`.
   Auto-captions are unpunctuated; read for content, not style.
4. If there is no transcript yet for an episode (video lands ~1h after audio; bridge runs 3x/day),
   use `description` from episodes.json and mark `"source": "show-notes"`. With a transcript, mark
   `"source": "transcript"`. Never mark `websearch-fallback` again; that path is retired.

Ledger entries now carry `"podcast": "<slug>"`. Existing entries without it are AI Daily Brief.

## Step 2 — Decide if it's worth an email

For each new episode, judge it against `config.filtering`. The bar: **could JR do something
differently at work tomorrow because of this episode?** News about a funding round, a lawsuit, or
a model's benchmark scores does not clear it. "How to get the most out of Sonnet 5" does.

NLW often puts the tactical material in the **back half** of an episode, after the news read.
Weight the later portion accordingly — an episode whose first ten minutes are pure news may still
be the most actionable one of the week.

How I AI is the opposite shape: nearly every episode is a guest demoing a real workflow on screen,
so the bar is usually cleared. The risk there is vagueness, not news. Pull the guest's **literal**
prompt text, tool chain, file structure, or checklist from the transcript; a tactic that says
"they used Claude Code with a CLAUDE.md" is not finished until the rule itself is written out.

If nothing clears the bar, record the episodes in the ledger with `"actionable": false` and a
one-line reason, commit, and **send no email**. A quiet night is a correct outcome, not a failure.
Do not pad a thin episode to justify a send.

## Step 3 — Extract the tactics

Work from the fullest source available: transcript > show notes/description. Note which one you
used — extraction confidence depends on it.

For each tactic, capture:

- **The tactic** — one sentence, in the speaker's actual claim (NLW, or the How I AI guest), not a
  generalization of it
- **Why it works** — the mechanism, one or two sentences. Skip if the episode doesn't give one;
  don't invent a rationale.
- **Ready-to-paste artifact** — the part that matters. Not a description of the technique, but the
  thing itself:
  - for **Claude web/desktop** → the literal prompt text, in a fenced block, ready to copy
  - for **Claude Code** → the CLAUDE.md rule, slash-command file, or terminal workflow it becomes
  - pick whichever fits the tactic; some warrant both, most warrant one
- **JR's angle** — one line on where this lands in his work. He does Claude Code enablement for
  Salesforce CSMs and AEs (see `index.html` in this repo). A tactic that makes a customer demo
  sharper is worth more than one that only helps a researcher.

Quality bar: if a reader would have to think about how to apply the artifact, it isn't finished.
Fill in the specifics — real scenarios from JR's world, not `[YOUR TASK HERE]` placeholders.

**But this repo is public.** Write to the *shape* of his work, never its contents: "a renewal-risk
account", not the account's name; "a CSM onboarding deck", not the customer's. No customer or
prospect names, no deal specifics, no internal metrics, roadmap, pricing, or anything from a
Salesforce system. The tactic is what's worth keeping; the proprietary particulars are what make it
concrete in the moment, and they don't need to live in git history to do that.

If a tactic can't be made useful without a specific detail, put the generic version in the library
and keep the specific one in the email only.

**Do not invent tactics.** If the episode yields one good technique, report one. A short honest
email beats a padded one, and padding is what turns this into another unread newsletter.

## Step 4 — Update the library

Append to `podcast-insights/technique-library.md`, newest section at the top, following the format
already in the file.

Before appending, check for duplicates across BOTH podcasts: NLW returns to the same themes, and How
I AI guests often demo the same tool, and the library is only
useful if it doesn't say the same thing eleven times. If a tactic materially repeats one already
in the library, **update the existing entry** — sharpen it, add the new episode as a second source,
note what's new — rather than adding a near-copy. Genuine refinements of an old idea are worth
recording; restatements are not.

## Step 5 — Pick the one thing

Choose **a single tactic** for JR to try on his next working day. Criteria, in order:

1. Can be tried in under 15 minutes
2. Touches work he's actually doing (Claude Code enablement, customer-facing material)
3. Has a visible result — he can tell whether it worked

The draft arrives at 7pm, after his workday. Frame this as **tomorrow**, never "today."

If a night produces several strong tactics, still pick one. The point is that one thing gets tried,
not that five get skimmed.

## Step 6 — Leave the draft

Create a Gmail draft with `mcp__Gmail__create_draft`:

- **to**: `config.delivery.to` — if it is still `REPLACE_WITH_WORK_EMAIL`, **stop**: write the
  library and ledger, commit, and tell JR the address is unset instead of drafting to nobody.
- **subject**: `{subject_prefix} — {episode title}` (trim to something readable)
- **htmlBody**: the digest, plus a plain-text `body` alternative

Structure, in this order — the one thing comes first because it's the part that gets acted on:

1. **Try tomorrow** — the single tactic, with its paste-ready artifact inline
2. **Also from this episode** — remaining tactics, each with its artifact
3. **Episode** — podcast, title, date, link, and which source (transcript / show-notes) it came from
4. A link to the library file for anything older

Keep the prompts in `<pre>` blocks so they survive copy-paste out of the email intact. That is the
whole point of the artifact — if it arrives mangled, the tactic doesn't get used.

The Gmail connector cannot send. The draft sits in `config.delivery.from_account` for JR to send.

## Step 7 — Commit

Commit the library and ledger to `claude/podcast-insights-automation-wqfioa` and push with
`git push -u origin claude/podcast-insights-automation-wqfioa`. Retry network failures up to 4
times with exponential backoff (2s, 4s, 8s, 16s).

Commit message: what was extracted, not that the job ran.
Good: `Add 3 prompting tactics from NLW's Sonnet 5 episode`
Bad: `Daily podcast run`

Do not open a pull request.

---

## Notes

- **Never send an email for an episode already in the ledger.** Duplicates are the fastest way to
  make JR stop reading these.
- If several days went unprocessed, handle them in one pass and one email — not one email per day.
- If the same tactic keeps recurring across episodes or across the two shows, say so in the email.
  That repetition is itself signal.
- Bridge data is refreshed by Jilly's Mac at 5:00, 12:00, 18:00 ET (`~/.config/feed-bridge/`). If it
  is stale for 2+ nights, the fix is on the Mac, not in this routine.
