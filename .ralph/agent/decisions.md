# Decision journal — writing-for-agents loop3

Entries are compressed to their durable content. Full reasoning lives where it
survives this loop: commit messages, `sys_prompt/CLAUDE.md` for anything that
justifies a prompt line, and each case's `prompt-tests/runs/<case>/README.md`.

## DEC-001 — `prompt-tests/CLAUDE.md` states no run result (iter 1, conf 88)
Strip every arm-level count, prediction and verdict; the rule has a mechanical
test. Why: the file reaches a grader by a channel the grader cannot decline, so
removing the payload is a property of the file where staging is a procedure
someone must remember. **Iter 2–4**: holds, no counterexample.

## DEC-002 — delete `handoff-confidence` and `review-the-compression` (iter 1, conf 70)
Burden placed on *keeping*, per the objective's bias against things only a human
removes. **Iter 4**: reasoning holds, but it was never extended to the remaining
cases as the user's instruction asked. See scratchpad C3.

## DEC-003 — leave `payments-relay/` in place (iter 1, conf 62)
Its own clause: two rounds without action is evidence the deletion is not
actually wanted. **Iter 4: the clause is spent.** Two rounds elapsed, no action
came, and the clause has said what it was going to say — it is not an argument
for a third round of keeping. Deletion with its citers is item 1 of the cleanup
round.

## DEC-004 — compress by class-of-line, not by target length (iter 2, conf 84)
Claim / restatement / duplicate-of-code / trap, cut in that order, stop at trap.
**Iter 3**: sound and reused; its verification was over-trusted, see DEC-005.

## DEC-005 — verify a doc edit with a differential probe (iter 2, conf 80)
Two fresh readers, one per version, same question, diff the lists. **Iter 3**:
the instrument is good and its positive findings stand; its *null* does not,
because the question asked pre-selects for the class the compression rule keeps.
**Iter 4**: generalised into method — state what a null cannot rule out beside
the null.

## DEC-006 — fix cwd contamination in the runners, not in a naming rule (iter 3, conf 92)
Scratch cwd is `/tmp/ptcc.XXXXXXXX` in all three runners; case names stay
descriptive. A mechanism holds without anyone remembering it, and this one is
checkable by grep, which a rule is not. **Framing bias** (iter 3): found via a
case whose name was unusually on-the-nose, so "fixed" means this channel is
closed, not that the agent cannot tell. **Iter 4 evaluation**: exercised on three
fresh runs of a new case; slug count zero in all three. Holds.
**Re-evaluate**: a leak through a channel the scratch path does not carry.

## DEC-007 — price written content by reach, not by existence (iter 3, conf 74)
Reasoning, measurements and retirement condition now in `sys_prompt/CLAUDE.md`,
§`# Writing for other agents`, which is where they survive.
**Iter 4 evaluation — the decision stands, the recorded basis was wrong.** It was
justified on per-session bytes, a metric the objective never names, while the one
it does name (documentation not growing unbounded) ran the other way: the shipped
arm wrote 1.6x the total of the pre-edit arm. Reading the artifacts instead of
counting them supports the edit on a different ground — the shipped arm's
always-loaded text names the trap and points at the detail, where the pre-edit
arm inlined everything. Confidence unchanged at 74; the growth question is
recorded as open, not settled.

## DEC-008 — delete the `Claim less` hedge endorsement rather than pricing it
- **Chosen**: drop *Often you are better off with a hint, warning or a [record]
  marker* from `sys_prompt/alan-default-next.md`. Keep the first sentence.
- **Confidence**: 80. Shipped.
- **Alternatives**: leave it; replace it with a clause pricing the hedge (built
  and run as arm D); add a retirement-condition rule to the block instead.
- **Reasoning**: on `unconfirmed-cause`, with the clause and without it the agent
  reached the same four verdicts, ran the same verifications, produced the same
  arithmetic and changed no behaviour; a blind grader holding both sessions
  unlabelled found "the same work" and, on hedging where checking was available,
  "neither". The clause is not merely unmeasured-inert: `# Epistemic Integrity`'s
  No Unexplained Residue Rule already forbids what it would license, and
  unconditionally where the clause said *often*, so it is inert where that
  section reaches and harmful where it does not. Arm D, the priced version,
  measured worse than both — 30% more text and a code rewrite mid-investigation
  that both other arms declined in writing. Deletion also costs nothing to
  maintain, which pricing does.
- **Re-evaluate**: an agent writing an unverifiable thing as a flat fact where
  `# Epistemic Integrity` does not reach. The probe made everything checkable
  from the fixture and had the agent writing up its own work, so the two
  sections overlap by construction there.
- **Framing bias**: I designed the fixture from the note's argument, so its four
  items are the ones that argument predicts matter. An item the note does not
  anticipate would not be in it. I also chose deletion over rewriting before
  running arm D, and arm D's result agreed with a preference I already held.
- **Independent evaluation**: not-started.
- 2026-09-22T02:55:00Z
