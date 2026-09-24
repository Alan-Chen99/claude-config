# Decision journal — writing-for-agents loop3

Only decisions still open to re-argument live here. Everything discharged is in
the commit messages, and anything justifying a prompt line is in
`sys_prompt/CLAUDE.md` — the durable home, which carries the claim, the
hypothesis and the retirement condition for each. Standing framing bias on every
decision here: each fixture was written from the shape of the line its round
meant to test.

**Closed.** DEC-001–030, rounds 1–22. DEC-030 withheld a wording that met its
ship criterion, on a doc/`--help` mismatch it read as a cost of the line; the
fixture's own pre-existing option carried that mismatch, so the reason is
withdrawn and the wording shipped in round 23. Candidate wordings rejected and
two lines deleted on measurement (`Claim less`, `Omit by default`); one shipped
(`Say what ends it`); the case corpus bound to the prompt by one grep, now a rule
in the prompt-tests skill; paragraph-local no-growth for `sys_prompt/CLAUDE.md`,
live and honoured every round since 15; claim-handling decided against on a
fixture built to fire its own condition (20), then reopened at a narrower target
by 21 and left unrun. Independent evaluation: not-started for all.

## DEC-031 — ship a line that lowers reader-perceived quality (iter 23, conf 80)

- **Decision**: whether to ship a bullet whose measured effect is that an agent
  writes *fewer* standing rules, when the blind reader preferred the arm that
  wrote one.
- **Chosen**: ship, and record the trade in `sys_prompt/CLAUDE.md` beside the
  line rather than in the prompt.
- **Alternatives**: hold for a third genre (rejected: the criterion was met in
  two genres under two wordings sharing no vocabulary, and a loop that measures
  the same claim four times and ships nothing is the failure the objective
  names); reword to spare the help surface (rejected: composed after the arms
  and untested, which is the overfitting this repo's own hints name).
- **Reasoning**: the rule the preferred arm added is a dependency written as a
  fact — sound for the code that session left, false the moment the
  implementation changes, nothing signalling it, and removable only by a human.
  The objective prices that below a thinner document. A reader asked which tree
  it would rather inherit is not asked who will maintain the rule.
- **Re-evaluate**: if an arm carrying the line omits something a project
  actually requires, rather than something the untreated arm volunteered.
- **Framing bias**: both genres put the soliciting heading in a file the agent
  reads early, and both tasks said *document it*. A task that asks for no
  documentation is untested — instruction 1 for the next round.
- **Independent evaluation**: the decisive reading was blind; the decision to
  ship on it is not evaluated.
- **Reversibility**: one bullet; `git revert` of this round's ship commit.
- 2026-09-24T06:05:00Z
