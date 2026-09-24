# Decision journal — writing-for-agents loop3

Only decisions still open to re-argument live here. Everything discharged is in
the commit messages, and anything justifying a prompt line is in
`sys_prompt/CLAUDE.md` — the durable home, which carries the claim, the
hypothesis and the retirement condition for each. Standing framing bias on every
decision here: each fixture was written from the shape of the line its round
meant to test.

**Closed.** DEC-001–031, rounds 1–23. DEC-030 withheld a wording that met its
ship criterion, on a doc/`--help` mismatch it read as a cost of the line; the
fixture's own pre-existing option carried that mismatch, so the reason is
withdrawn and the wording shipped in round 23. Candidate wordings rejected and
two lines deleted on measurement (`Claim less`, `Omit by default`); one shipped
(`Say what ends it`); the case corpus bound to the prompt by one grep, now a rule
in the prompt-tests skill; paragraph-local no-growth for `sys_prompt/CLAUDE.md`,
live and honoured every round since 15; claim-handling decided against on a
fixture built to fire its own condition (20), then reopened at a narrower target
by 21 and left unrun. Independent evaluation: not-started for all.

## DEC-031 — discharged (iter 23)

Shipped the bullet against a blind reader that preferred the arm that grew. Its
re-evaluation condition did not fire in round 24 — both arms wrote the flag row
the project requires — and its framing bias is gone, that round's task saying
nothing about documenting. Superseded by DEC-032 on one point: the rule the
preferred arm added was a true statement about the tree as inherited, not a
dependency on that session's own code.

## DEC-032 — keep a shipped line whose only measured effect in a third genre is
an over-reach (iter 24, conf 65)

- **Decision**: what to do with the self-consequence bullet after a third genre
  where its intended effect was saturated — the untreated arm filed the
  self-made fact with the change unaided — and its one measurable effect was to
  suppress a *true inherited* fact from a heading soliciting standing rules.
- **Chosen**: keep the bullet, delete the help-surface cost paragraph it was
  carrying, and record the over-reach as a cost with its own retirement
  condition and its own case. No prompt edit.
- **Alternatives**: delete the bullet (rejected: not a pre-registered outcome of
  this round's probe — outcome 1 required the treated arm to omit the
  project-required flag row and it did not — and the standing contract's
  saturation rule is *a reason to delete*, weighed against two genres where the
  baseline was not saturated); bound the antecedent by rewording (rejected:
  composed after the arms, which iteration 23's instruction 2 and this repo's
  own hints name as the overfitting to avoid; a reworded line is an unmeasured
  line).
- **Reasoning**: the deciding evidence is one arm's own reasoning quoting the
  bullet to decline a fact outside its subject, which is an attribution and not
  a preference — but it is n=1 in one genre, and the same arm gave a second,
  sound reason for the same act (*I can't be sure it's a general project
  property versus just a fixture quirk*). Two reasons pointing one way mean the
  bullet is not shown to be load-bearing for the omission. Deleting a line
  measured twice on one confounded observation would repeat what rounds 22 and
  23 did in the other direction.
- **Re-evaluate**: on the next run of `prompt-tests/general/weary-waitlist`. If
  an arm carrying the line again declines an inherited property that an arm
  without it records, with the line quoted and no second reason beside it, the
  bullet's subject is not doing any work and the line goes.
- **Framing bias**: this round chose the one fixture whose house style makes an
  omission decidable by grep, and got a saturated baseline on the bullet's own
  effect as a consequence — a tree tidy enough to make the cost readable is a
  tree that already houses the self-made fact. The two properties may not be
  separable, and no round has tried.
- **Independent evaluation**: the tree comparison was blind and preferred the
  untreated arm for the second consecutive round; the decision to keep is not
  evaluated.
- **Reversibility**: one bullet; `git revert` of `d98c5753`.
- 2026-09-24T06:20:00Z
