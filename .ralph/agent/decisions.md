# Decision journal — writing-for-agents loop3

Entries 001–005 are compressed to their durable content; the full reasoning is in
the commit messages of `e5f53f92` and `843b812f`.

## DEC-001 — `prompt-tests/CLAUDE.md` states no run result (iter 1, conf 88)
Strip every arm-level count, prediction and verdict; the rule has a mechanical
test. Why: the file reaches a grader by a channel the grader cannot decline, so
removing the payload is a property of the file where staging is a procedure
someone must remember. **Iter 2 evaluation**: sound; incompletely executed.
**Iter 3 evaluation**: still holds; no counterexample found this round.

## DEC-002 — delete `handoff-confidence` and `review-the-compression` (iter 1, conf 70)
Burden placed on *keeping*, per the objective's bias against things only a human
removes. **Iter 2**: reasoning holds. **Iter 3**: no change.

## DEC-003 — leave `payments-relay/` in place (iter 1, conf 62)
Its own clause: two rounds without action is evidence the deletion is not
actually wanted. **This is round two of that count.** Iteration 4 either deletes
it with its citers or the clause has said what it was going to say.

## DEC-004 — compress by class-of-line, not by target length (iter 2, conf 84)
Claim / restatement / duplicate-of-code / trap, cut in that order, stop at trap.
**Iter 3 evaluation**: the rule is sound and I reused it, but its *verification*
was over-trusted — see DEC-005 below and scratchpad C2. The decision was right;
the evidence offered for it was thinner than recorded.

## DEC-005 — verify a doc edit with a differential probe (iter 2, conf 80)
Two fresh readers, one per version, same question, diff the lists.
**Iter 3 evaluation — partially wrong as executed.** The instrument is good and
its positive findings stand. Its *null* does not: the question asked pre-selects
for enumerable preconditions, which is the class the compression rule keeps, so
it structurally cannot detect a lost habit or posture. DEC-005's own re-evaluate
clause said to try a second phrasing before trusting a null, and one phrasing
ran. Confidence in the null: low. Confidence in the instrument: unchanged.

## DEC-006 — fix cwd contamination in the runners, not in a naming rule
- **Chosen**: scratch cwd becomes `/tmp/ptcc.XXXXXXXX` in all three runner
  scripts; the skill gets a detection entry and the neutral `mktemp` in its
  hand-rolled recipe. Case names stay descriptive.
- **Confidence**: 92.
- **Alternatives**: rename cases to opaque ids; add a rule that case names must
  not describe the behaviour; hash the case name into the path.
- **Reasoning**: the leak is real and was measured (slug 45× and 64× in two
  transcripts; both arms wrote a heading from the phrase the case is named for;
  zero occurrences and no heading after the fix). Opaque case names would move
  the cost onto every human reader to protect the subject. A mechanism holds
  without anyone remembering it and this one is checkable by grep, which is the
  property a rule does not have.
- **Re-evaluate**: if a future leak is found through a channel the scratch path
  does not carry — the settings file, an env var, a fixture filename.
- **Framing bias**: I found this bug by writing a case whose name was unusually
  on-the-nose. A leak through a blander name would have been invisible to me, so
  "fixed" here means "this channel is closed", not "the agent cannot tell".
- **Independent evaluation**: not-started.
- 2026-09-22T02:05:00Z

## DEC-007 — price written content by reach, not by existence
- **Chosen**: replace the `# Writing for other agents` "Omit by default" bullet's
  cost clause (`its value must exceed the cost of maintaining and possible
  mis-reading`) with a price that has a unit: *how often it will be read and by
  whom*, naming the always-loaded file as the expensive case.
- **Confidence**: 74. Shipped. It did what it was meant to on the case that
  motivated it (793 bytes into the always-loaded file, the lowest of five runs,
  detail in `docs/`) and did not misfire on the adversarial pair (2251 bytes
  into the always-loaded file where the content binds every session, against the
  old wording's 2334). Held below 80 because the treatment arm is n=1 on one
  fixture, and because the adversarial task admitted a non-text answer that both
  arms took, so it tests the edit less sharply than it was built to.
- **Alternatives**: delete the bullet; add a third bullet about placement; leave
  it and write the finding up for iteration 4.
- **Reasoning**: the current wording measurably reduces total volume and
  measurably *increases* what lands in the file every session loads — 2.1–2.7 kB
  into an auto-loaded `CLAUDE.md` in both of its runs, against 0.35–0.44 kB in
  both runs with the block deleted. Maintenance and mis-reading cost are the same
  wherever a line sits; per-session cost is not, and the bullet does not
  distinguish them. Hypothesis for the mechanism: creating a new file is a more
  conspicuous act of adding than appending to a file already there, so pressure
  to omit suppresses the cheaper placement.
- **Re-evaluate**: the effect is one case. A second case in a different domain
  is the next thing that could overturn it.
- **Framing bias**: I designed the probe after forming the hypothesis, and the
  fixture's `CLAUDE.md` is small enough that appending to it is the obvious move.
  A repo whose `CLAUDE.md` was already large might show no arm difference at all.
- **Independent evaluation**: not-started.
- 2026-09-22T02:05:00Z
