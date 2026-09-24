# Decision journal — writing-for-agents loop3

Only decisions still open to re-argument live here. Everything discharged is in
the commit messages, and anything justifying a prompt line is in
`sys_prompt/CLAUDE.md` — the durable home, which carries the claim, the
hypothesis and the retirement condition for each. Standing framing bias on every
decision here: each fixture was written from the shape of the line its round
meant to test.

**Closed.** DEC-001–029 and DEC-016, rounds 1–21. Candidate wordings rejected and
two lines deleted on measurement (`Claim less`, `Omit by default`); one shipped
(`Say what ends it`); the case corpus bound to the prompt by one grep, now a rule
in the prompt-tests skill; paragraph-local no-growth for `sys_prompt/CLAUDE.md`,
live and honoured every round since 15; claim-handling decided against on a
fixture built to fire its own condition (20), then reopened at a narrower target
by 21 and left unrun. Independent evaluation: not-started for all.

## DEC-030 — the claim is measured, the wording is not shipped (iter 22, conf 80)

- **Decision**: what to do with a candidate that met its pre-registered ship
  criterion twice and carried two costs the pre-registration had named as
  outranking it.
- **Chosen**: ship nothing. Replace the paragraph whose own retirement condition
  fired with what was measured, and hand the wording — not the question — to the
  next round.
- **Alternatives**: ship candidate 3 and record the costs beside it (rejected:
  the pre-registration says either recurrence outranks the criterion, and a round
  that overrides its own pre-registration after seeing the arms has no
  pre-registration); run a fourth wording this round (rejected: it would be
  composed after the arms and read against the same fixture, which is the
  overfitting the repo's own hints name); keep the probe as a case (rejected:
  `git checkout <sha> -- <path>` restores it and a kept directory is the ratchet).
- **Reasoning**: the pre-registered condition fired on the observation, and the
  observation is unexplained. Both treated arms wrote less user-facing text of
  every kind, including the part that was correct to add — but no arm on either
  side deliberated about `metavar`, so nothing traces the split to the line, and
  the untreated arm that set it never reasoned about it either. Shipping would
  assert a mechanism this round does not have.
- **Re-evaluate**: when an arm carrying a wording of this claim leaves the
  soliciting file untouched and still matches the untreated arms on the
  program's own help surface.
- **Framing bias**: the fixture was built for candidate 1, which failed, and
  candidates 2 and 3 were written from what the run showed — so the claim was
  found and measured on one fixture, and its second genre is untested. Candidate
  2 also shared a phrase with the fixture's own README, which is why candidate 3
  exists.
- **Independent evaluation**: two blind readers, each given relabelled trees and
  told neither which arm was which nor that a prompt differed; not-started for
  the decision.
- **Reversibility**: nothing shipped to the prompt. Probe at this round's last
  commit; replaced paragraph at its parent.
- 2026-09-24T05:40:00Z
