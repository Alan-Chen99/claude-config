# Decision journal — writing-for-agents loop3

Only decisions still open to re-argument live here. Everything discharged is in
the commit messages, and anything justifying a prompt line is in
`sys_prompt/CLAUDE.md` — the durable home, which carries the claim, the
hypothesis and the retirement condition for each.

**Closed.** DEC-001–027, rounds 1–18. Six candidate wordings rejected and two
lines deleted on measurement (`Claim less`, `Omit by default`); one shipped
(`Say what ends it`, now isolated); the case corpus bound to the prompt by one grep (DEC-023,
now a rule in the prompt-tests skill); paragraph-local no-growth for
`sys_prompt/CLAUDE.md` (DEC-019, live and honoured every round since 15).
Framing bias on all of them: each fixture was written from the shape of the line
its round meant to test. Independent evaluation: not-started.

## DEC-028 — keep `Say what ends it`; its predicted harm was looked for and is not there (iter 19, conf 76)
- **Chosen**: two arms on the case this line's own retirement condition names —
  HEAD, and HEAD minus the bullet with the preamble kept. Ship no prompt edit;
  record the isolation in `sys_prompt/CLAUDE.md`, paid for by compressing the
  paragraph beside it.
- **Alternatives**: retire on outcome 4, whose antecedent did fire — the treated
  arm applied one retirement template to all four rows, the bare preference
  included (rejected: outcome 4's *harm* half was an assertion borrowed from the
  case's reference, and the blind reader preferred the uniform arm on exactly
  that row); call the run undetermined because 1 and 4 both fired (rejected: the
  facts of both are recorded and the disposition turns on a claim the blind
  reading contradicts); a third arm to separate the `quality-reviewer` dispatch
  the treated arm made (rejected: the exits predate it, call 22 against 26).
- **Reasoning**: the only line the loop had shipped and the only one never
  isolated, so the one thing a round could both falsify and remove. It survived
  at the row its own hypothesis names, with the two observation-ended rows going
  to both arms unaided — that internal agreement is what makes n=1 readable.
- **Re-evaluate**: when an arm carrying it names no more exits than one without,
  on `prompt-tests/general/retirement-policy`. Also when a fixture puts a
  *second* item with no picturable end beside the preference — the thin exit the
  template writes there is the nearest thing to a cost this run saw.
- **Framing bias**: I came into the round expecting to delete, having read two
  rounds of deletions; the outcome table I wrote let a keep and a retire fire
  together, which is the shape of a round that had not decided what it was
  measuring. The blind reader is the only reason the R4 row was not scored as a
  harm on my say-so.
- **Independent evaluation**: one blind reader, stock Claude Code with an empty
  config so it did not carry the line under test; not-started for the decision.
- **Reversibility**: nothing shipped to the prompt. The replaced paragraph is at
  `4eae4b69^`; the run is at `b71737f7`.
- 2026-09-22T09:35:00Z
