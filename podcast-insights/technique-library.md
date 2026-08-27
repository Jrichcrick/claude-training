# AI Daily Brief — Technique Library

Everything actionable NLW has said that JR wanted to keep. Newest first.

Populated nightly by `/podcast-insights`. Hand-edits are welcome — the automation appends and
refines, it never rewrites the file wholesale.

**How to use this:** search it. When you're about to do something at work — write a customer
prompt, set up a CLAUDE.md, structure a demo — grep this file for the thing you're doing first.
That's the whole reason it exists rather than living in your inbox.

---

## Status

**Pending backfill:** the **Fable 5 / GPT-5.6** episode — how to get the most out of both models,
including running a task through a batch of prompts. The tactics are in the back half. It's the
reason this automation exists, and it aired before the automation did, so the nightly job won't
pick it up on its own. Ask for it once the feed host is allowlisted (see `README.md`) and it'll be
extracted and added here.

---

## 2026-08-27 — AI Daily Brief episode on Stanley Druckenmiller's AI-written WSJ op-ed and NLW's five rules for AI writing (exact episode title unconfirmed)

**Source:** search coverage (podcast hosts still blocked at the proxy — see README). Independently
corroborated: 3 of NLW's 5 rules ("different types of writing, different types of rules"; "the
purity test will die, the quality test won't"; "longer is not better — usually the opposite") and 2
of the use-case crib-sheet items (emails, strategy memos). The other 2 rules and the social/
marketing-copy/op-ed crib-sheet entries didn't surface with independent corroboration across
queries, so they're left out here rather than guessed at — this is a partial extraction of a real
episode, not a complete one.
**Link:** https://aidailybrief.ai/e/2026-08-27

### 1. Get the thesis fully worked out before AI drafts a word — then run a dedicated pass to scrub AI-isms

NLW's framing, hung on Stanley Druckenmiller's WSJ op-ed (an AI detector scored it 100%; the Journal
published it anyway and said it broke no policy; Druckenmiller's answer when asked was "of course I
used AI"): AI writing goes wrong not because AI wrote it, but because the writer skipped straight to
"draft this" without doing the thesis work first. Get extremely clear on your actual argument and
the points that support it — NLW's line was "the five-paragraph essay from grade school, baby" —
*before* handing it to the model. Then, separately, go back through and scrub the obvious AI-isms.

**Why it works:** a model asked to draft without a real argument to execute will invent generic
structure and phrasing to fill the gap — that's where the AI-isms a detector catches actually come
from. A worked-out thesis gives it something specific to execute instead of something to invent, and
treating the scrub as its own deliberate pass — not a hope that it drafted clean — is what catches
what a detector would.

**For Claude web/desktop:**

```
I want to draft [a renewal-risk update email / a QBR prep memo / a LinkedIn post about a product
launch — name the actual thing], and I want to do it in a way that doesn't read as AI-written.

Before you draft anything, make me work out the thesis first — ask me these three questions and
don't draft until I've answered them (if my answers are vague, push back and make me sharpen them):
1. What is the one sentence this needs to argue or communicate?
2. What are the 3-4 points that support it, in the order that makes the strongest case?
3. What's the one thing I most want the reader to do or believe after reading it?

Once I've given you a real thesis and supporting points, draft it in [email / memo / post] form,
built tightly around exactly that thesis — no padding, no generic scene-setting.

Then run a second pass as a skeptical editor scrubbing specifically for AI-isms: flag anything that
reads as generic filler, over-hedged, unnecessarily long, or in a voice that doesn't sound like
something I'd actually say out loud to this reader. Show me what you'd cut or rewrite and why,
rather than silently fixing it.
```

**JR's angle:** this is a two-minute habit JR can run on the exact things his job produces daily —
an enablement follow-up email, a customer-facing one-pager, a demo script — and it gives him a
concrete answer, not a preachy one, the first time a CSM asks "won't this just sound like AI":
show the thesis-first draft next to a bare "write me an email about X" draft, side by side.

### 2. Match the AI-writing rule to what the document is actually for, not one blanket policy

Two of NLW's use-case notes, independently confirmed: **emails are safe territory for AI** (though
he notes dictation might actually beat it for speed) because an email is judged on being useful and
fast, not on showing your thinking. **Strategy memos are "sneakily bad" for AI** — a memo's entire
value is demonstrating the judgment behind it, and a fully AI-drafted one can read fine while
quietly skipping the actual thinking it was supposed to capture. NLW's broader point: the "purity
test" (was AI involved, yes/no) is a dead question after a Journal-published, admittedly AI-assisted
op-ed drew a shrug — the "quality test" is the one that survives, and it gives a different answer
depending on the format.

**Why it works:** treating "AI or not" as one policy across every kind of writing ignores that
different documents are judged on different things — speed and clarity for an email, demonstrated
judgment for a memo. The habit that's harmless in one is quietly self-defeating in the other.

**For Claude Code — a CLAUDE.md rule:**

```markdown
## AI-writing rule, by document type

Check what kind of document this is before drafting, and apply the matching rule — don't use one
blanket approach for all writing:

- **Emails / quick internal updates:** full AI drafting is fine. Optimize for speed and clarity,
  not for demonstrating that a human agonized over it.
- **Strategy memos / QBR prep notes / anything meant to show my judgment:** don't fully draft this
  from a one-line ask. Ask me for my actual reasoning and the calls I made first (why this account,
  why this recommendation, what I'd do if I'm wrong) and draft it around my real thinking, not a
  plausible-sounding stand-in for it. If I try to skip straight to "just write it," push back once
  and ask what my actual take is before drafting.
- **Customer-facing marketing copy / social posts:** draft freely, but flag anything that reads as
  generic AI phrasing before I send it — this is exactly the kind of document readers are primed to
  detect it in.
```

**JR's angle:** a CLAUDE.md starting point JR can hand a CSM or AE directly, and it doubles as a
demo talking point for the governance question customers actually ask ("should we even let people
use AI for X") — answered with a rule instead of a blanket yes/no.

---

## 2026-08-14 — How to Decide What Work AI Should Do for You: The AI Deputization Audit

**Source:** search coverage (podcast hosts still blocked at the proxy — see README)
**Link:** https://aidailybrief.ai/e/2026-08-14

### 1. Score recurring work on five axes, then sort it into hand-off / partner / keep — not gut feel

NLW's framing: for any recurring task, score it 0-10 on five dimensions — **frequency** (how often
it happens and how long it takes), **teachability** (could you show someone the whole thing in a
ten-minute screen share?), **checkability** (how long does verifying the output take compared to
doing the task yourself?), **stakes** (how bad is it if AI gets it wrong and nobody catches it?),
and **how much it needs to be you** (is your specific judgment actually the thing that makes the
output good?). Add it up: **deputize the 8-10s** — hand them to AI, spot-check for a while, then
stop checking. **Defend the 0-3s** — those stay yours. **Duet on everything in the middle**, which
is where NLW says most knowledge work actually lives.

**Why it works:** "should I let AI do this?" is usually answered by instinct, and instinct is
inconsistent — the same person will delegate a high-stakes task on a good day and hoard a trivial
one on a bad day. A shared scoring rubric turns that gut call into something repeatable and
arguable, which matters most exactly where the answer isn't obvious (the "duet" middle, not the
easy extremes).

**For Claude web/desktop:**

```
I want to run my recurring work through a delegation framework called the AI Deputization Audit,
then apply it to a real list of tasks.

The rubric — score each task 0-10 on five axes:
1. Frequency: how often does it happen, and how long does it take each time?
2. Teachability: could you show someone the entire task in a 10-minute screen share?
3. Checkability: how long does verifying the output take, compared to just doing the task yourself?
4. Stakes: how bad is it if AI gets this wrong and nobody catches it before it goes out?
5. "Needs to be you": is your specific judgment the thing that actually makes the output good, or
   is it a process anyone competent could execute?

Scoring: average the five, or note if one axis (usually stakes) should override the others on its
own. 8-10 = deputize (hand it off, spot-check for a couple weeks, then stop checking). 0-3 = defend
(keep it, don't delegate). Everything else = duet (AI drafts or assists, you stay in the loop on
every instance).

Worked example so you know the level of detail I want back — a weekly "how's this account doing"
update for a renewal-risk customer:
- Frequency: 9 (weekly, ~45 min each time)
- Teachability: 8 (pull usage data, check it against last week, flag what changed — easy to show)
- Checkability: 7 (skimming for a wrong number or an over-claimed win takes 5 min, writing it takes 45)
- Stakes: 5 (goes to an internal channel, not the customer directly — wrong once isn't a crisis, but
  wrong repeatedly erodes trust in the update itself)
- Needs to be you: 4 (the judgment about what's worth flagging is learnable from a few examples;
  it doesn't require context only I have)
→ Average ~6.6, stakes doesn't override → duet: draft it, I review before it posts.

Now here's my actual list of recurring tasks: [paste your list — one line each is fine, doesn't
need to be formatted]

Score each one on the five axes, give me the bucket (deputize / duet / defend) and a one-line
reason, and flag any where stakes alone should override the average.
```

**JR's angle:** this is a demo-ready framework, not just a personal productivity trick — when a CSM
or AE is stuck at "I don't know what to actually hand to Claude Code," this gives them a rubric to
run in the room instead of a vague pep talk. It also reframes the sell: Claude Code enablement isn't
"automate your job away," it's "score your own recurring work and see where you're already
over-defending things that would score an 8." Worth pairing with a live pass through 3-4 of a
customer's own recurring tasks in a demo rather than talking about the framework in the abstract.

**Ledger note:** this episode was misidentified in the 2026-08-15 run as unrelated regulation/China
policy content (see `processed.json`, the now-superseded `regulation-china-ai-politics-*` entry for
2026-08-14) — that was a bad WebSearch match, not a second episode. This entry corrects it; the
regulation/China content, whatever its actual source, contained no extractable tactic either way.

---

## 2026-08-12 — Grok Bot Finally Makes AI Agents Easy

**Source:** search coverage (podcast hosts still blocked at the proxy — see README)
**Link:** https://aidailybrief.ai/e/2026-08-12

### 1. Teach an agent a workflow by demonstration, not by upfront spec — then turn it into a reusable command

NLW's framing: the computer-use agents in this episode learn a workflow the same way a new hire
would — you do the task once while it watches, and it saves what it saw as an editable routine you
refine with corrections, rather than you trying to write a complete procedure before it ever runs.

**Why it works:** describing a task accurately in a prompt, up front, is harder than doing the task
— you skip steps that feel obvious to you but aren't written down anywhere. Demonstrating it once
captures the real order of operations; corrections after the fact are cheap compared to getting the
spec right on the first try.

**For Claude Code:**

```
I want to turn a task I just walked you through into a reusable slash command.

Here's what I did, step by step, as I did it:
[narrate the task in the order you did it — e.g. "First I pulled the account's last few adoption
touchpoints from my notes. Then I checked which Claude Code features they'd actually turned on
versus what's included in their license. Then I drafted three lines: what's working, what's sitting
unused, and one specific next step tied to an outcome they've said they care about."]

Turn this into a slash command:
1. Name it something short and specific to what it does.
2. Write it as a step-by-step procedure I can run again on a different account — generalize the
   specifics I gave you into "the account" / "the customer" language, not the literal names or
   numbers I used.
3. Call out anywhere I made a judgment call (what counted as "working," how I picked the one next
   step) as an explicit decision point in the command, so future-me knows what to weigh, not just
   what to type.
4. Tell me what someone else running this command should always double check before sending or
   acting on its output — bake that in as an explicit review checklist at the end, not an
   afterthought.
5. Tell me the exact file it should live in and the command name I'd type to run it.
```

**JR's angle:** most CSMs stall out at "write a slash command from scratch" — it feels like a
programming task. This reframes it as "just talk me through what you already do once," which is a
much lower-friction pitch in a demo, and it's exactly how JR can turn his own recurring prep work
(account health checks, enablement one-pagers) into commands instead of redoing them from memory
each time.

**Update (2026-08-25):** a second episode ("What the Top AI Users Are Doing Differently,"
https://aidailybrief.ai/e/2026-08-25) independently arrives at the same core move from a different
angle — OpenAI's enterprise usage data, which NLW covers directly, shows the gap between top and
typical AI users has widened from 2.6x to 8.3x output per user, and attributes it to frontier firms
turning individuals' effective ad hoc AI usage into documented, repeatable, team-wide processes with
review built in from the start, rather than leaving good habits locked in one person's head. That's
this same tactic, not a new one — logged here as a second, quantified source rather than a
duplicate entry. It's also the reason step 4 above (the review checklist) was added: the earlier
version of this command didn't force that step, and NLW's framing this time made explicit that
skipping it is exactly what separates a one-off habit from something a team can actually run.

### 2. Calibrate an agent's escalation threshold through correction, not upfront rules

NLW's description of how these agents earn trust over a few tasks: they pick up on writing style,
edge cases, and — the part worth stealing — when to interrupt you versus just keep going, purely
from being corrected after the fact rather than from a rule written in advance.

**Why it works:** nobody can enumerate every case where an agent should stop and ask first; trying
produces either a rule so long it's ignored or one so short it misses the case that mattered. Acting
first and treating a correction as the new default is faster to converge and cheaper to maintain.

**For Claude Code — a CLAUDE.md rule:**

```markdown
## Escalation calibration

Don't try to guess my judgment-call threshold from a spec — you won't get it right on the first
try, and neither would I trying to write it. Instead:

- When you're unsure whether something needs my sign-off (sending anything customer-facing,
  changing a number in a deliverable, picking between two reasonable approaches), default to
  asking the first few times you hit that kind of situation.
- When I correct you — "you didn't need to check with me on that" or "you should have asked before
  doing that" — add a one-line rule below under "Escalation rules," describing the pattern, not the
  one-off instance.
- Once a pattern has a rule here, stop asking about it and just apply the rule.

### Escalation rules
(empty until the first correction — this section is meant to grow from what actually happens, not
from guessing in advance)
```

**JR's angle:** "how do I trust it to just handle things" is the objection JR hears most from
customers piloting Claude Code past the demo stage. This turns that into a concrete answer — trust
isn't a perfect prompt, it's a couple of corrections — and gives him a CLAUDE.md block he can hand a
customer directly instead of just describing the idea.

*Related:* the "chief of staff plus specialist agents" structure this episode also describes is the
same ownership/handoff idea as entry 2 below (2026-08-10) — recorded there, not duplicated here.

---

## 2026-08-10 — What the Heck is Graph Engineering?

**Source:** search coverage (podcast hosts still blocked at the proxy — see README)
**Link:** https://aidailybrief.ai/e/2026-08-10

### 1. Use the prompt → context → harness → loop → graph ladder to diagnose a misbehaving AI workflow

NLW's framing: every stage of working with AI has minted its own "engineering" discipline — prompts
control the instructions, context controls what the model sees, the harness controls the
environment it acts in, loops control iteration, and graph engineering is the newest rung, which
controls the agentic organization itself. When something isn't working, the ladder is a checklist
for where the actual problem lives, rather than a reason to keep rewriting the prompt.

**Why it works:** a workflow that's failing at the context or harness layer looks identical, from
the outside, to one that's failing because of bad prompt wording — so the default fix (edit the
prompt again) often lands on the wrong layer. Naming the layers turns a vague "it's not working"
into a specific question: which layer is actually broken?

**For Claude web/desktop:**

```
I'm troubleshooting an AI workflow that isn't behaving the way I want, and I don't want to just
keep rewriting the prompt and hoping something changes.

Here's the situation: [describe it — e.g. "a Claude Code agent that's supposed to update an
Opportunity's next-step notes after a customer call, but it keeps skipping the update or writing
it to the wrong field"].

Walk me through it layer by layer, and for each one tell me whether it's a likely culprit and what
a fix at that layer would concretely look like:

1. Prompt — is the instruction itself ambiguous, or missing a case it needs to handle?
2. Context — is the model missing information it needs to see (the right fields, the right
   history, a concrete example of "done right")?
3. Harness — is the surrounding tool or environment giving it the wrong permissions, inputs, or
   feedback about whether it succeeded?
4. Loop — does this need iteration/self-checking that it isn't getting, or is it iterating when it
   should just do the task once?
5. Graph — is this actually too much for one agent, and does it need to be split into multiple
   agents with an explicit handoff?

Tell me which layer is most likely the real problem — not just where a fix is easiest to try — and
give me the smallest concrete change to test first.
```

**JR's angle:** this is a sharper response than "let's tweak the prompt" when a CSM says their
Claude Code setup "isn't doing what I told it to." It gives him a fast triage question to ask
before touching anything, and it's a genuinely useful mental model to hand to a customer who's
about to hit the same wall themselves.

### 2. Before splitting work across agents, write the graph in three lines: owners, handoffs, failure behavior

NLW's description of graph engineering itself: it's the layer that decides which agents exist,
what each one owns, how work moves between them, and — the part that's easiest to skip — what
happens when a step fails. The claim is that this should be designed explicitly, on purpose,
rather than emerging by accident as a workflow grows past one agent.

**Why it works:** an ad hoc chain of agents tends to leave failure handling implicit — nobody
decided what happens if step two produces something step three can't use, so it just breaks
downstream in a confusing way. Writing the three things down before building forces that decision
to happen on purpose.

**For Claude Code:**

```
## Agent graph for [workflow name]

Before adding a second agent to this workflow, write out the graph in three lines:

- **Owners** — for each agent, one line naming exactly what it owns and nothing else
  (e.g. "research-agent owns pulling account history; drafting-agent owns writing the outreach
  email; drafting-agent does not touch account data directly").
- **Handoffs** — what one agent passes to the next, stated as actual fields/format, not "the
  output" (e.g. "research-agent hands drafting-agent a bullet list of the last 3 account touches,
  not a paragraph summary").
- **Failure behavior** — for each agent, what happens if it fails or produces something the next
  agent can't use: retry once, escalate to a human, or stop the whole graph. Do not leave this
  implicit.

Do not touch prompts for the individual agents until these three lines are written.
```

**JR's angle:** directly useful for any multi-step Claude Code demo he builds for CSMs/AEs — e.g.
a research-then-draft pipeline for prepping a renewal-risk account. Having the three-line graph on
a slide before showing the code answers "why would I need more than one agent here?" in a way that
clicks faster than watching the agents run.

---

## 2026-08-02 — Everything You Need to Know About AI Tokens (Operator's Cut, with Nufar Gaspar)

**Source:** search coverage (podcast hosts still blocked at the proxy — see README)
**Link:** https://podcasts.apple.com/us/podcast/the-ai-daily-brief-artificial-intelligence-news/id1680633614 (show page — the specific episode URL couldn't be confirmed with hosts blocked)

### 1. Track cost per successful task, not raw token spend

Gaspar's framing: agentic workflow costs don't spiral because tokens are expensive — they spiral
because teams measure the wrong thing. Aggregate token/dollar totals hide where the money actually
went; the fix is to anchor cost to *cost per completed, successful task*, not cost per token
consumed.

**Why it works:** a raw spend total buries failed and retried attempts inside one number. Once you
divide spend by successful outcomes instead of by tokens, the workflows that are actually expensive
(lots of failed attempts per success) become visible, separate from workflows that only look
expensive because of general usage volume.

**For Claude web/desktop:**

```
I want to evaluate whether an agentic AI workflow is actually cost-effective for a specific task —
say, a support engineering team using Claude Code to triage and fix a category of recurring bugs.

Instead of estimating total token spend, walk me through:
1. What "success" looks like for this task — the deliverable, not the attempt
2. A rough framework for cost per successful completion, assuming some attempts fail or need a retry
3. What would make cost-per-success go up over time, and how I'd notice it in a real deployment
   before it became a problem

Keep this framed as a cost-per-outcome conversation, not a token-counting exercise — I want
language I can use with a customer who's worried costs will spiral as they scale usage.
```

**For Claude Code:**

```
## Cost accountability

When running a multi-step or agentic task, log the outcome alongside the cost:
- Note whether the task succeeded, partially succeeded, or failed
- Track cost per attempt, including retries, not just the final attempt
- Before reporting a task "done," state the cost against the successful outcome —
  not the cumulative cost of every attempt it took to get there

This makes wasted retries visible instead of buried inside one aggregate spend number.
```

**JR's angle:** cost objections ("won't this get expensive as we scale agents?") are one of the
most common blockers CSMs and AEs hear once a pilot moves toward wider rollout. This gives a
sharper answer than "tokens are cheap" — a way to reframe the conversation around cost-per-outcome,
which is also a number a customer's own finance stakeholders will find more legible than a raw
usage bill.

### 2. Kill "tokens that spin" — cap unproductive agent retries

Gaspar's term for the other big source of waste: tokens burned in loops where an agent retries the
same failing approach repeatedly instead of stopping or trying something materially different. Left
unbounded, this is where agentic cost actually spirals — not from doing more work, but from doing
the same failed work over and over.

**Why it works:** without an explicit stop condition, agent tooling defaults to retrying on
failure. Retries that repeat the same strategy add cost without adding a chance of success; capping
them turns an open-ended cost risk into a bounded, predictable one.

**For Claude Code:**

```
## No unbounded retries

If an agentic task fails validation, retry with a materially different approach at most twice.
If a subsequent attempt would use the same strategy as a prior failed attempt, stop and report
failure with what was tried — do not keep retrying the same thing. A task that stops and reports
honestly is cheaper than one that silently spins.
```

**JR's angle:** good live-demo material. Showing a prospect that Claude Code can be configured to
stop and report rather than silently burn budget directly answers the "what stops this from running
away on cost" question that comes up in almost every agent-adoption conversation.

---

## Entry format

Each episode that clears the actionable bar gets one section:

```markdown
## YYYY-MM-DD — Episode title

**Source:** transcript | show notes | search coverage
**Link:** https://...

### 1. Name of the tactic

The claim, in one sentence, as NLW actually made it.

**Why it works:** the mechanism, if the episode gives one.

**For Claude web/desktop:**

​```
The literal prompt text, filled in with real specifics — ready to paste, no placeholders.
​```

**For Claude Code:**

​```
The CLAUDE.md rule, slash command, or terminal workflow this becomes.
​```

**JR's angle:** where this lands in Claude Code enablement work.

### 2. Next tactic
...
```

Not every tactic needs both a chat prompt and a Claude Code artifact — most warrant one. Include
whichever the tactic actually is.

---

## Recurring themes

When a tactic shows up in more than one episode, it gets noted here rather than duplicated above.
Repetition across episodes is signal: it's what NLW keeps coming back to.

**Demonstration-based skill capture and the AI Deputization Audit are becoming NLW's core
framework, not one-off segments.** The 2026-08-16 episode ("The New Problems AI Is Creating (And
How People Are Solving Them)") returned to both: GrokBot's teach-a-task and ChatGPT's Computer
History as the same "show it once, it becomes a reusable skill" idea as the 2026-08-12 entry, and
"Deputize, don't automate — step one: inventory your recurring processes" as the on-ramp to the
full five-axis rubric in the 2026-08-14 entry. Nothing new enough to extract on its own, but two
recaps in three episodes is a sign these are the two frameworks NLW treats as load-bearing right
now — worth leading with either one if a demo needs a single anchor framework.
