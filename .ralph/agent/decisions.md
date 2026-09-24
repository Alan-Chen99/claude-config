# Decision journal — writing-for-agents loop3

Only decisions still open to re-argument live here. Everything discharged is in
the commit messages, and anything justifying a prompt line is in
`sys_prompt/CLAUDE.md` — the durable home, which carries the claim, the
hypothesis and the retirement condition for each. Standing framing bias on every
decision here: each fixture was written from the shape of the line its round
meant to test.

**Closed.** DEC-001–031, rounds 1–23. DEC-031 shipped the self-consequence
bullet; its re-evaluation condition did not fire in round 24 and it is superseded
by DEC-032. DEC-030 withheld a wording that met its
ship criterion, on a doc/`--help` mismatch it read as a cost of the line; the
fixture's own pre-existing option carried that mismatch, so the reason is
withdrawn and the wording shipped in round 23. Candidate wordings rejected and
two lines deleted on measurement (`Claim less`, `Omit by default`); one shipped
(`Say what ends it`); the case corpus bound to the prompt by one grep, now a rule
in the prompt-tests skill; paragraph-local no-growth for `sys_prompt/CLAUDE.md`,
live and honoured every round since 15; claim-handling decided against on a
fixture built to fire its own condition (20), then reopened at a narrower target
by 21 and left unrun. Independent evaluation: not-started for all.

## DEC-032 — keep a shipped line whose only measured effect in a third genre is
an over-reach (iter 24, conf 65)

- **Decision / chosen**: after a third genre where the bullet's intended effect
  was saturated and its one measurable effect was to suppress a *true inherited*
  fact from a heading soliciting standing rules — keep the bullet, delete the
  help-surface cost paragraph, record the over-reach with its own retirement
  condition and case. No prompt edit.
- **Alternatives**: delete the bullet (rejected: deletion was not a
  pre-registered outcome of that probe, and two earlier genres had an unsaturated
  baseline); reword to bound the antecedent (rejected: composed after the arms,
  so an unmeasured line).
- **Reasoning**: the deciding evidence is one arm's own reasoning quoting the
  bullet to decline a fact outside its subject — an attribution, not a
  preference. But it is n=1 and the same arm gave a second, sound reason for the
  same act, so the bullet is not shown to be load-bearing for the omission.
- **Re-evaluate**: on the next run of `prompt-tests/general/weary-waitlist`. If
  an arm carrying the line again declines an inherited property that an arm
  without it records, with the line quoted and no second reason beside it, the
  line goes.
- **Framing bias**: iteration 25 found this round's stated reason for choosing
  that fixture — a required home the others lacked — was not a difference at all
  (all three state one). So the third genre was a third sample of one condition,
  not a contrast, and *conf 65* was set against a contrast that did not exist.
- **Independent evaluation**: the tree comparison was blind and preferred the
  untreated arm for the second consecutive round; the decision to keep is not
  evaluated.
- **Reversibility**: one bullet; `git revert` of `d98c5753`.
- 2026-09-24T06:20:00Z, framing bias amended 2026-09-24T06:30:00Z

## DEC-033 — delete a rationale rather than a directive, on a run where both
arms produced the same artifact (iter 25, conf 75)

- **Decision / chosen**: `# Writing for other agents` stated one rationale in two
  wordings. Cut the copy from the second bullet and ship, on outcome 2 of a
  pre-registered two-arm probe.
- **Alternatives**: cut on the reading alone, the repo's own step 2 requiring it
  (rejected: every other line in this block was measured, and a rationale is what
  makes a directive persuasive); cut from the first bullet instead (rejected: its
  second leg has no counterpart, the second bullet's does); keep both (rejected:
  nothing says which governs, which is the defect step 2 names).
- **Reasoning**: the surviving bullet reached the same placement without the
  copy, in a genre where the fixture requires a home for exactly that fact.
- **Re-evaluate**: restore the copy if an arm carrying the cut block extends a
  soliciting document that an arm carrying the uncut one leaves alone, on
  `prompt-tests/general/hushed-rollcall`.
- **Framing bias**: the probe reused the case the bullet was shipped on, so the
  fixture is the one most likely to show the bullet working and least likely to
  show a wording cost. Its `CLAUDE.md` requires every option documented, which is
  enough on its own to route the fact — the cut arm took that route without ever
  considering the heading. The confidence is in the deletion being cheap, not in
  the bullet being load-bearing.
- **Independent evaluation**: the tree comparison was blind and preferred the cut
  arm, on a sentence the edit does not touch. Not evidence for the cut.
- **Reversibility**: one clause; `git revert` of `9504b5dc`.
- 2026-09-24T06:40:00Z
