# podcast-insights

Extract implementable tactics from new episodes of **The AI Daily Brief** (NLW), add them to
JR's technique library, and leave a finished email draft addressed to his work address.

Runs nightly at ~7:07pm ET via a Routine. Also runnable by hand: `/podcast-insights`.

Read `podcast-insights/config.json` first — it holds the feed, the recipient, the filter rules,
and the audience context. Config wins over anything hardcoded below.

---

## Step 0 — Make sure you have the repo

The Routine fires a fresh session whose primary repo is `nyc-marathon-2026`, not this one. If
`/workspace/claude-training` is not present:

1. `add_repo` with owner `Jrichcrick`, repo `claude-training`, access `push`
2. `git clone --depth 1 https://github.com/jrichcrick/claude-training /workspace/claude-training`
   (generous timeout, one attempt)
3. `git -C /workspace/claude-training checkout claude/podcast-insights-automation-wqfioa || git -C /workspace/claude-training checkout -b claude/podcast-insights-automation-wqfioa`

Always `git pull` the branch before editing so you build on the previous night's ledger.

## Step 1 — Find what's new

Resolve the feed:

- If `config.podcast.feed_url` is set, use it.
- Otherwise resolve it: `https://itunes.apple.com/lookup?id=1680633614` → `results[0].feedUrl`.

Fetch the feed. Take every episode published since `processed.json.last_run_utc` (first run: just
the most recent 3). Drop any whose GUID already appears in `processed.json.episodes`.

**If the feed is unreachable** — the proxy returns 403 on CONNECT for a host the network policy
doesn't allow — do not silently produce nothing. Fall back to `WebSearch` for the episode title
and any published summary, mark the entry `"source": "websearch-fallback"` in the ledger, and say
so plainly at the top of the email so JR knows the extraction is thinner than usual. If even that
fails, write the ledger with `"status": "unreachable"` and skip the email.

## Step 2 — Decide if it's worth an email

For each new episode, judge it against `config.filtering`. The bar: **could JR do something
differently at work tomorrow because of this episode?** News about a funding round, a lawsuit, or
a model's benchmark scores does not clear it. "How to get the most out of Sonnet 5" does.

NLW often puts the tactical material in the **back half** of an episode, after the news read.
Weight the later portion accordingly — an episode whose first ten minutes are pure news may still
be the most actionable one of the week.

If nothing clears the bar, record the episodes in the ledger with `"actionable": false` and a
one-line reason, commit, and **send no email**. A quiet night is a correct outcome, not a failure.
Do not pad a thin episode to justify a send.

## Step 3 — Extract the tactics

Work from the fullest source you can reach: transcript > full show notes > description > search
coverage. Note which one you used — extraction confidence depends on it.

For each tactic, capture:

- **The tactic** — one sentence, in NLW's actual claim, not a generalization of it
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

**Do not invent tactics.** If the episode yields one good technique, report one. A short honest
email beats a padded one, and padding is what turns this into another unread newsletter.

## Step 4 — Update the library

Append to `podcast-insights/technique-library.md`, newest section at the top, following the format
already in the file.

Before appending, check for duplicates: NLW returns to the same themes, and the library is only
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
3. **Episode** — title, date, link, and which source the extraction came from
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
- If the same tactic keeps recurring across episodes, say so in the email. That repetition is
  itself signal about what NLW thinks matters.
