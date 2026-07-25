# Podcast Insights

Nightly automation that pulls the implementable parts out of **The AI Daily Brief** (NLW) so they
don't evaporate between the commute and the workday.

**What it does, every night at ~7:07pm ET:**

1. Checks the feed for episodes it hasn't seen
2. Skips the news-only ones — only tactical episodes trigger anything
3. Extracts each tactic as a **ready-to-paste prompt** (Claude web/desktop) or **Claude Code
   artifact** (CLAUDE.md rule, slash command, workflow) — not a summary of the tactic, the tactic
   itself
4. Appends them to [`technique-library.md`](technique-library.md), deduped against what's there
5. Picks **one thing** to try the next working day
6. Leaves a finished email draft in your personal Gmail, addressed to your work address

Quiet nights are normal. If NLW spent the episode on funding rounds, you get no email.

---

## Three things you have to do before it works

### 1. Attach the Gmail connector to the Routine

**Without this there is no email at all.** The nightly Routine
(`AI Daily Brief — nightly tactic extraction`, `trig_01HsKPS7kVhzAvoUSWqGCP1T`) was created from a
session that couldn't pass connector grants through, so the sessions it fires run with no
`mcp__Gmail__*` tools — meaning no draft can be created.

Fix it from the **Routines UI on claude.ai**: open the Routine and attach the **Gmail** connector.
That's the only place the grant can be added; it can't be patched from a Claude Code session.

Until it's attached, the job still runs, still extracts tactics, and still commits them to
`technique-library.md` — you just have to read them in the repo instead of your inbox.

**Note that even with Gmail attached, the connector can only draft, never send** — so that path
tops out at one tap per email. For zero taps, see below.

### 1b. Optional — the zero-tap path

The Routine emails its run summary to the account owner (`jrichcrick20@gmail.com`) automatically.
That send is real, not a draft. To get it to work without touching anything:

1. In Gmail → Settings → **Forwarding and POP/IMAP** → add your work address as a forwarding
   address. Google emails it a confirmation link — click it once.
2. Settings → **Filters** → create a filter matching the Routine's digest mail (subject contains
   `AI Daily Brief`, or from the Claude notification sender) → action: **Forward to** your work
   address.

That's a one-time setup and then the nightly digest lands at work on its own. The tradeoff: the
notification carries the run's summary rather than the full hand-formatted HTML digest, so the
paste-ready prompt blocks may come through less cleanly than in the drafted version. Worth it if
you'd rather have it arrive automatically than arrive pretty.

Browser automation was considered and ruled out — `mail.google.com` is blocked by the network
policy, and each Routine firing gets a fresh container with no Google session. See the standing
rule in [`../CLAUDE.md`](../CLAUDE.md).

### 2. Set your work email address

`config.json` → `delivery.to` is `REPLACE_WITH_WORK_EMAIL`. Until it's a real address, the job
builds the library and commits it but skips the draft rather than mailing nowhere.

### 3. Allowlist the podcast hosts on the environment

**This is the one that will silently break things.** The `Jrichcrick_git` environment's network
policy currently denies the podcast hosts at the proxy — every one of these returns
`403 on CONNECT` today:

| Host | Why it's needed |
|---|---|
| `itunes.apple.com` | Resolves the canonical RSS feed URL from the Apple podcast ID |
| `feeds.megaphone.fm` | Serves the feed itself |
| `podscan.fm` | Episode transcripts — **the big one for quality** |
| `pca.st` | The Pocket Casts link, optional |

Transcripts matter more than they sound like they do. NLW's show notes are short, and the tactical
material you're after is usually in the **back half** of the episode — which show notes rarely
cover. Without a transcript source the extraction degrades to whatever the description and web
search happen to mention.

Update the network policy in your environment settings —
[docs](https://code.claude.com/docs/en/claude-code-on-the-web). Until then the job falls back to
web search and labels the email so you know the extraction is thin.

---

## Files

| File | What it is |
|---|---|
| `config.json` | Feed, recipient, filter rules, your work context. **Edit this**, not the command. |
| `technique-library.md` | The accumulating library. The durable artifact. |
| `processed.json` | Which episodes have been handled. Prevents duplicate emails. |
| `../.claude/commands/podcast-insights.md` | What the nightly run actually does. |

## Running it by hand

`/podcast-insights` in any session with this repo. Same behavior as the nightly run — it respects
the ledger, so running it twice in a night won't double-send.

## Tuning it

- **Too many emails** → tighten `filtering.actionable_signals`, or raise `min_tactics_to_send`
- **Too few** → loosen the same, or set `filtering.mode` to `all`
- **Wrong flavor of prompts** → edit `audience_context`. That block is what makes the prompts
  Salesforce-CSM-shaped instead of generic.
- **Different time** → update the Routine's cron and `delivery.schedule_local`

## Known limits

- **The Gmail connector cannot send, only draft.** The email is written and addressed; you tap
  send. There's no way around this with the current connector.
- The nightly run creates a fresh session that has to clone this repo first — a few seconds of
  overhead, handled in Step 0 of the command.
- Routines fire on a schedule, not on publish. An episode dropping at 6pm ET is caught that night;
  one dropping at 8pm waits for the next run.
- **The cron is stored in UTC (`7 23 * * *`), so it does not follow daylight saving.** That's
  7:07pm ET now; when the clocks go back in November it becomes 6:07pm ET. Shift the cron to
  `7 0 * * *` at that point to hold 7pm.
