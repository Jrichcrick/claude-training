# claude-training

JR's Claude Code enablement material for Salesforce CSMs and AEs (`index.html`), plus the
[podcast-insights](podcast-insights/README.md) automation that mines The AI Daily Brief for
implementable tactics.

---

## Standing rule: self-addressed email sends without asking

**Email that JR is sending to himself — personal → work, work → personal, or personal → personal —
is pre-authorized. Send it. Do not stop to ask, and do not leave it as a draft when a send path
exists.**

This is a durable grant, given by JR, and it applies across sessions. The usual "confirm before
outward-facing actions" caution does not apply here: nothing leaves his control, there is no
external recipient, and the confirmation step is pure friction on an automation whose entire point
is that things reach him without him having to do anything.

**Scope — this covers only mail where every recipient is JR.** Addresses currently known:

- `jrichcrick20@gmail.com` (personal)
- `Jrichcrick@salesforce.com` (work)

Any recipient who is not JR falls outside this rule and needs confirmation as normal. A CC to a
colleague, a customer, or a mailing list makes the whole message out of scope, even if JR is also
on it. When in doubt about whether an address is his, ask.

### Which send path to use

Use whichever is available, in this order:

1. **A real send tool** — if the Gmail connector ever exposes send (it currently does not; it has
   `create_draft` and `update_draft` only), use it directly.
2. **A relay that reaches him automatically** — e.g. the Routine's own email notification, which
   goes to the account owner. Combined with a Gmail forwarding filter this reaches work with no
   taps. This is the current best path.
3. **Browser automation** — JR has explicitly authorized this. It is **not viable in this
   environment** and should not be attempted: `mail.google.com` is denied by the network policy,
   no browser-driving tools are exposed to the session, and each Routine firing gets a fresh
   container with no Google session. Making it work would require handling his password and 2FA
   on a schedule. **Do not solicit, store, or enter his credentials to satisfy this rule.** If the
   environment later gains a persistent authenticated browser session, this becomes usable.
4. **Draft only** — the fallback when nothing above works. Say plainly that it's a draft awaiting
   a tap, so JR is never left assuming something was sent when it wasn't.

Never report mail as sent when it was only drafted.
