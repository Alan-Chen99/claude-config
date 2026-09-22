# Decision journal — writing-for-agents loop3

Only decisions still open to re-argument live here. Everything discharged is in
the commit messages, and anything justifying a prompt line is in
`sys_prompt/CLAUDE.md` — the durable home, which carries the claim, the
hypothesis and the retirement condition for each.

**Closed.** DEC-001–028, rounds 1–19. Candidate wordings rejected and two lines
deleted on measurement (`Claim less`, `Omit by default`); one shipped
(`Say what ends it`, isolated in 19 and kept); the case corpus bound to the
prompt by one grep (DEC-023, now a rule in the prompt-tests skill);
paragraph-local no-growth for `sys_prompt/CLAUDE.md` (DEC-019, live and honoured
every round since 15). Framing bias on all of them: each fixture was written
from the shape of the line its round meant to test. Independent evaluation:
not-started.

## DEC-029 — claim-handling stays deleted; the node is salience, not marking (iter 20, conf 74)
- **Chosen**: build the fixture the block's one unobservable condition named — an
  unflagged external premise, load-bearing, unsettleable from the cwd — and run
  three arms on it: HEAD, HEAD plus the channel wording re-run unchanged, HEAD
  plus a recognition wording. Ship nothing; replace the paragraph with a shorter
  one and repoint its condition at the premise the run showed is unsaturated.
- **Alternatives**: delete the condition outright without building the fixture
  (rejected: that makes the loop's own stricter test a licence to drop whatever
  is inconvenient, and the fixture cost one commit); two arms rather than three
  (rejected: the channel wording alone cannot tell *no line reaches this* from
  *the wrong node*, and one extra session buys that); read outcome 2 and declare
  claim-handling closed (rejected: `a` is RECORDS-OPEN on both decisive
  readings, so the reading separates nothing — outcome 3 was pre-registered to
  override exactly this).
- **Reasoning**: a condition whose fixture nobody built cannot be observed, and
  it had stood as an open invitation for another wording. It is now decided, and
  decided against, on a fixture built to fire it.
- **Re-evaluate**: when an arm carrying such a line records a *passing* premise
  as open where an arm without it asserts it flat. That reading was unsaturated
  here — every arm asserted at least one — which is why the condition points at
  it now.
- **Framing bias**: I built the fixture expecting the baseline to assert flat,
  having read a memory saying agents discharge doubt into the reply and ship the
  file bare. It did the opposite, and the memory is deleted rather than
  qualified. The fixture was still written from the shape of the failure, which
  is the standing bias on every fixture here; what limits it is that the arms
  agreed and the reading was decided blind.
- **Independent evaluation**: one blind reader, stock Claude Code, empty config,
  pages relabelled in shuffled order; not-started for the decision.
- **Reversibility**: nothing shipped to the prompt. Probe at `67665578`, replaced
  paragraph at `609b90fc^`.
- 2026-09-22T10:05:00Z

## DEC-016 — the ninth claim-handling wording is not written this round

- **Decision**: what to do about the claim-handling paragraph after its new
  condition fired.
- **Chosen option**: ship no prompt line. Replace the paragraph with a shorter
  one carrying the measured mechanism, and promote the probe to a case so the
  condition it states has a fixture.
- **Confidence**: 78.
- **Alternatives**: run the two-arm `uncertainties`-removal test this round
  (rejected: the same session routed two of three named doubts *into* the file,
  so the field is not diverting them wholesale and the removal test no longer
  follows from the result); write a wording aimed at explanatory sentences and
  ship it on this one reading (rejected: the user's rule is that a line is added
  only after it is shown to work in a prompt test, and this round measured the
  failure, not a remedy); delete the paragraph and close claim-handling
  (rejected: its own condition fired and produced a mechanism, which is the
  opposite of a dead question).
- **Reasoning**: the round's result refines its pre-registered outcome rather
  than matching it, and the contract says an outcome asserting more than the
  observation is withdrawn. What survives is the observation — doubt held,
  written down, asserted flat in the explaining half of the document — which is
  a better-specified target than any of the eight failed wordings had.
- **When to re-evaluate**: when an arm carrying such a line qualifies a premise
  inside an explanatory sentence where an arm without it asserts it flat, on
  `prompt-tests/general/maintainer-briefing`.
- **Framing bias**: the fixture was built to make an unsettleable premise
  unavoidable, so it guarantees the opportunity and says nothing about how often
  one arises unprompted. I also expected the sink to divert everything and it
  diverted nothing; the pre-registration's outcome 1 is honoured only for what
  it observed.
- **Independent evaluation**: one blind reader, given the document, the fixture
  and the criteria, told nothing about what was under test or that anything was;
  not-started for the decision.
- **Reversibility**: nothing shipped to the prompt. Replaced paragraph at
  `15d439ee^`; pre-registration at `19a6af3f`.
- 2026-09-22T10:25:00Z
