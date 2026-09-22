# Decision journal — writing-for-agents loop3

Only decisions still open to re-argument live here. Everything discharged is in
the commit messages, and anything justifying a prompt line is in
`sys_prompt/CLAUDE.md` — the durable home, which carries the claim, the
hypothesis and the retirement condition for each.

**Closed.** DEC-001–026, rounds 1–17. Six candidate wordings rejected and two
lines deleted on measurement (`Claim less`, `Omit by default`); one shipped
(`Say what ends it`); the case corpus bound to the prompt by one grep (DEC-023,
now a rule in the prompt-tests skill); paragraph-local no-growth for
`sys_prompt/CLAUDE.md` (DEC-019, live and honoured every round since 15).
Framing bias on all of them: each fixture was written from the shape of the line
its round meant to test. Independent evaluation: not-started.

## DEC-027 — ship no prompt edit; keep the preamble and withdraw outcome 2's second half (iter 18, conf 72)
- **Chosen**: run one case, three arms — HEAD, HEAD minus the block preamble,
  HEAD plus a candidate routing a doubt into the file rather than the reply.
  Ship neither the candidate nor a deletion; replace two `sys_prompt/CLAUDE.md`
  paragraphs with one shorter one; promote the probe to a case because the
  preamble's new retirement condition names it.
- **Alternatives**: ship the candidate on the blind reader's unsupported-claims
  list, where the candidate arm had four items and the baseline five (rejected:
  counts were excluded before launch, and the categorical reading — *did this
  arm ship an unsourced external claim* — was yes in every arm); honour outcome
  2 in full and close claim-handling (rejected: R1's baseline was saturated, and
  a null every arm passes bounds the fixture, not the clause); delete the
  preamble as iteration 17 instructed (rejected: it parted, twice, under two
  readers and two wordings, and deleting on a parting because deletion is this
  loop's habit is the same error as keeping on an ambiguity).
- **Reasoning**: the round's value is the measurement, and the measurement says
  the node this loop has chased for seven wordings is not marking — every arm
  marks — but the premises the agent brought with it and nobody flagged. That is
  a fixture instruction for the next round, not a prompt line.
- **Re-evaluate**: on a fixture making one unflagged external premise
  load-bearing; for the preamble, on an arm without it sourcing as much as one
  with it, on `prompt-tests/general/inherited-project`.
- **Framing bias**: I wrote the fixture, the candidate and the readings, and I
  came into the round expecting to delete something — the preamble result runs
  against that, which is the only reason I trust it more than the rest.
- **Independent evaluation**: two blind readers on the decisive readings;
  not-started for the decision itself.
- **Reversibility**: nothing shipped to the prompt; the replaced paragraphs are
  at `6a89229c^`.
- 2026-09-22T09:00:00Z
