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

_(nothing yet)_
