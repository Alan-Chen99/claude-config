# writing-for-agents loop3 — scratchpad

## Where the objective bites

The sharpest clause is *things that do not require explicit human approval to add,
but require human intervention to remove*. Every other goal follows from that
ratchet. The question to carry into every decision is **what retires this line**.

## Durable method, reusable across rounds

**The compression rule.** Sort every line by what it is; cut in this order,
stopping at the first class that is load-bearing: (1) a **claim** — only claims
can be wrong; delete unless load-bearing and not cheaply re-derivable. (2) a
**restatement** — with two wordings nothing says which governs. (3) a **duplicate
of executable code** — replace with the script's name. (4) a **trap** — what the
reader gets wrong by default, silently. Keep. Deletion is the default; each
*keep* is what needs an argument.

**A line that names a consideration does not deliver the conclusion it argues
for.** It makes the consideration salient, and the agent then argues it in
whichever direction the task favours. Measured twice on `Omit by default`'s reach
wording: more readership reasoning, none of it reaching the clause's own
conclusion. *(iter 13)*

**A retirement condition names a comparison, not an observation.** "Retire this
when an arm carrying the line does no better than one without it" is the only
form a later round can act on.

**Buy resolution inside the run, not across runs.** At n=1 a fixture with one
opportunity for the behaviour under test yields a coin flip; several
opportunities that *differ in character* yield the policy the agent applied.

**Arms must differ in kind, not in degree.** *Wrote a second file or not*,
*issued an imperative or not*, *fact present in the loaded file or not* are
categorical and readable at n=1. A line count is a sample of the spread.

**A pre-registered exclusion binds hardest when the excluded number turns out to
be the only one favouring your prior.** Iteration 13 excluded line counts in
advance, then found they were the sole evidence for the wording it was cutting.
Recorded, not acted on. Reaching for it would have been a reading composed after
the arms were in. *(iter 13)*

**A criterion written from the shape of the failure cannot score a good
outcome.** Write what the good artifact looks like before what the bad one lacks.

**A prose warning inside the thing it warns about does not stop a reader who has
read it.** Convert to a refusal with an escape hatch; the refusal is checkable.

**A pre-registered outcome names the channel it is read from**, and a
pre-registered *reading* can be wrong. Withdrawing beats honouring.

**Test the lines already shipped, not only the candidates.** A shipped line with
a named, unmeasured harm outranks any new candidate.

**A clause no fixture can exercise is not an open question; it is a deletion
candidate with an outstanding test.** *(iter 13)*

## Standing `(contract)`

> An iteration may not spend its whole milestone on the prompt-test instrument
> unless that iteration also runs at least one arm against
> `sys_prompt/alan-default-next.md`.

> A prompt edit's justification lands in `sys_prompt/CLAUDE.md`, naming what would
> retire the line, in the same commit as the edit.

> An edit that deletes or renames anything a document can point at sweeps the tree
> for citers in the same commit — `grep -rn --include='*.md' <name> .` — and the
> commit says which were left on purpose.

> Each round either edits `sys_prompt/alan-default-next.md`, or writes into
> `sys_prompt/CLAUDE.md` what its own measurement showed that makes no edit the
> right call.

> Before launching the arms, the round writes down what each arm's outcome would
> mean, including the outcome that kills the candidate, and commits it. A reading
> composed after the arms are in is not admissible. Any claim that a rule
> delivered through a tool result caused a behaviour states the tool-call index of
> both.

> A round's runs are **probes** unless it argues otherwise: small fixture, one
> targeted question, read off the artifact by the round itself, no grader and no
> foci. A probe earns keeping only when a later round needs to re-run it.

> **A round that ships no prompt edit may not add a paragraph to
> `sys_prompt/CLAUDE.md`; it may replace one, and the replacement is shorter than
> what it replaced.**

> **A stored run is retired by the condition its own README states**, and the
> round that notices deletes the directory. The condition may not depend on a
> later round choosing particular work.

> **No claim in `sys_prompt/CLAUDE.md` may be a run narrative.** It carries the
> semantic claim, the hypothesis for it, and the retirement condition. Counts, arm
> labels, byte deltas, dates and fixture descriptions belong to the run's own
> README and to git.

> **An `(instruction)` asserting that work is undone states the command that
> shows it.** Iteration 12 handed forward "no round has done this" about a user
> ask that one grep refutes, and acting on it would have spent a round re-doing
> finished work. *(iter 13)*

## Rounds 1–13 — `9f6c03a0` → `f2737a34`

Detail is in commit messages; anything justifying a prompt line is in
`sys_prompt/CLAUDE.md`, which is the durable home and the one to read before
touching the block. Shipped: the `Claim less` hedge endorsement deleted (4),
`Say what ends it` added (9), `Omit by default` repriced to reach (3) and back
to existence (13). Rounds 6–8: three wordings aimed at claim-handling all failed
because the node is premise **provenance**, not wording. Round 10 fixed a
nine-round harness contamination and voided every arm stored before 2026-09-22.
Round 11: restatement grows by accretion, not addition. Round 12: the task's
subject bounds the edit, so relocation-as-growth cannot occur on a writing task.
Round 13 measured reach on two destinations, found no arm sorted by it, and cut
it; it also deleted `platform-portability` and repaired three colliding case
justifications.

