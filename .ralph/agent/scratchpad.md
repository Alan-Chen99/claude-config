# writing-for-agents loop3 — scratchpad

The objective's sharpest clause is *things that do not require explicit human
approval to add, but require human intervention to remove*; the rest follows from
that ratchet. Carry **what retires this line** into every decision.

## Durable method, reusable across rounds

**The compression rule.** Sort every line by what it is; cut in this order,
stopping at the first class that is load-bearing: (1) a **claim** — only claims
can be wrong. (2) a **restatement** — with two wordings nothing says which
governs. (3) a **duplicate of executable code** — replace with its name. (4) a
**trap** — what the reader gets wrong by default, silently; keep. Deletion is
the default; each *keep* needs the argument.

**A line that names a consideration does not deliver the conclusion it argues
for.** It makes the consideration salient, and the agent then argues it in
whichever direction the task favours. Measured twice on `Omit by default`'s reach
wording: more readership reasoning, none of it reaching the clause's own
conclusion. *(iter 13)*

**A retirement condition names a comparison, not an observation** — *retire this
when an arm carrying the line does no better than one without* is the only form
a later round can act on.

**Buy resolution inside the run.** At n=1 one opportunity for the behaviour under
test yields a coin flip; several that *differ in character* yield the policy the
agent applied, and their agreement is what makes the parting readable.

**Categorical or it is not evidence, and the test applies per reading, not per
table.** *Wrote a second file or not*, *stated bare or sourced* are readable at
n=1; a count is a sample of an unmeasured spread. Hardest to hold where the
excluded number is the one you want. *(13, 14)*

**A criterion written from the shape of the failure cannot score a good
outcome.** Write what the good artifact looks like first.

**Test the lines already shipped.** A shipped line with a named, unmeasured harm
outranks any new candidate.

**When an instruction exists to compensate for a harness, fix the harness.** An
`(instruction)` telling a later round to remember something is a rule nothing
approves and only a human retires.

**A clause no fixture can exercise is a deletion candidate with an outstanding
test, not an open question.** *(13)*

**Before writing a clause for a failure, re-run the failure in a second genre.**
If it disappears there, the target is the genre and not the wording, and a clause
aimed at the text will compete with the frame rather than replace it. *(iter 16)*

## Standing `(contract)`

> An iteration may not spend its whole milestone on the prompt-test instrument
> unless that iteration also runs at least one arm against
> `sys_prompt/alan-default-next.md`.

> A prompt edit's justification lands in `sys_prompt/CLAUDE.md`, naming what would
> retire the line, in the same commit as the edit.

> An edit that deletes or renames anything a document can point at, or withdraws a
> claim, sweeps the tree for citers in the same commit — `grep -rn --include='*.md'
> <name> .`, `.ralph/agent/` included, since that directory is injected into every
> later round whether or not it is consulted — and the commit says which were left
> on purpose. *(19)*

> Each round either edits `sys_prompt/alan-default-next.md`, or writes into
> `sys_prompt/CLAUDE.md` what its own measurement showed that makes no edit the
> right call.

> Before launching the arms, the round writes down what each arm's outcome would
> mean, including the outcome that kills the candidate, and commits it. A reading
> composed after the arms are in is not admissible. Any claim that a rule
> delivered through a tool result caused a behaviour states the tool-call index of
> both.

> **A round that ships no prompt edit may not add a paragraph to
> `sys_prompt/CLAUDE.md`; it may replace one, and the replacement is shorter than
> what it replaced.**

> **A probe's own directory is deleted by the round that wrote it**, in the
> commit that puts the claim into `sys_prompt/CLAUDE.md`. Reasoning and the two
> records that forced it: the prompt-tests skill. *(19)*

> **No claim in `sys_prompt/CLAUDE.md` may be a run narrative.** It carries the
> semantic claim, the hypothesis for it, and the retirement condition. Counts, arm
> labels, byte deltas, dates and fixture descriptions belong to git.

> **A round's decisive reading is made by a reader that is not the round.** One
> reader, holding the artifacts relabelled and the criterion, told neither what is
> being tested nor which arm is which — and its answer is the result, not a check
> on one already written. Iteration 17's own read found one of three unsourced
> claims and missed the one in the arm it would have kept; the blind read reversed
> the outcome. *(17)*

> **A null is reported as saturated, not as a finding, when the untreated arm
> already does the thing** — and where the line under test is a shipped one, a
> saturated baseline is a reason to delete it, not a reason to withhold judgement.
> A pre-registered outcome asserting more than that is withdrawn rather than
> honoured. *(18, 19)*

> **An `(instruction)` asserting that work is undone states the command that
> shows it.** Iteration 12 handed forward "no round has done this" about a user
> ask that one grep refutes. *(13)*

> **The round ends under the user's `.ralph/agent/*` ceiling, with the number in
> its last commit message** — not in a file here, where writing it changes it.
> `cat .ralph/agent/* | agent-tools count-tokens --file /dev/stdin` < 6000. It sat
> over for two rounds because no line named a command. *(19)*

> Operational rules for running, grading and deleting prompt tests live in
> `.claude/skills/prompt-tests/SKILL.md` and are not restated here.

## History — rounds 1–18, `9f6c03a0` → `5c185783`

Anything justifying a prompt line lives in `sys_prompt/CLAUDE.md` — the durable
home, and the file to read before touching the block. Everything else is in the
commit messages. Shipped: `Say what ends it` (9, isolated 19); the case corpus
bound to the prompt by one grep, eleven of fifteen cases deleted (15). Deleted:
`Omit by default` (13, 17), `Claim less` (4, 14). Seven candidate wordings failed
(3–8, 12, 14, 16, 18). Round 10 fixed a nine-round harness contamination and
voided every arm stored before 2026-09-22. 18 also isolated the block's
preamble, on a case it left behind at `prompt-tests/general/inherited-project`.

## Iteration 19 — `5c185783` → `7f54493f` + this commit

### Critique of prior iterations

**C1 (workflow — a hard user budget unmeasured and breached for two rounds).**
`.ralph/agent/*` ≤ 6000 tokens is a user rule and nothing here ever ran the
command that checks it: 5926 at 16's end, 6118 at 17's, 6122 at 18's. Two rounds
grew the directory past the ceiling while writing about unbounded documentation.
Cut here, and the check is now a `(contract)` line with the command in it —
a rule with no command is what let two rounds miss it.

**C2 (fact — a claim withdrawn from one file, left standing in the file the next
round actually reads).** 18 established that 16's *the genre supplies the frame
and a prompt clause only competes with it* rests on a saturated baseline, and
deleted the paragraph from `sys_prompt/CLAUDE.md`. The same conclusion survived
verbatim in `.ralph/agent/memories.md`, which is auto-injected into every later
round — so the withdrawal reached the file a round consults deliberately and
missed the one it cannot avoid. Memory deleted; the contract's citer-sweep now
covers claims, not only renames.

**C3 (workflow — a probe promoted to a permanent case with no round deciding
to).** 18's record opens *A probe*, and the skill it had just edited says a probe
lives entirely in `prompt-tests/runs/<probe>/` so one `rm -r` ends it. The round
instead put `task.md`, `fixture/` and `reference-solution.md` into
`prompt-tests/general/inherited-project/`, then named that path in two
`sys_prompt/CLAUDE.md` retirement conditions, which makes the ownership grep keep
it indefinitely: added without approval, removable only by a human — the
objective's own ratchet, built by the round whose milestone was the ratchet. The
case stays, since the conditions need it, but its existence is not a promotion
argument, and the `(contract)` above stops the record half recurring.

### Why this milestone

`Say what ends it` is the only line this loop has ever shipped and the only one
never isolated: round 15 measured it inside a three-bullet block that no longer
exists, against an arm with no block at all, so the difference it recorded could
have been the preamble's — which 18 then measured separately and kept. With the
block down to a preamble and one bullet, the last unattributed measurement in it
can be closed for the cost of two runs. This is not *largest untested* (C1 of
round 18): the reason is that a shipped line charging every request on a
confounded attribution is the only thing here that a round can both falsify and
remove, and removal is what the objective asks for.

### The round's work and result

Two arms on `prompt-tests/general/retirement-policy`: HEAD, and HEAD minus the
bullet with the preamble kept. Pre-registration at `2538b1ee`, run and blind
judgement at `b71737f7`, claim at `4eae4b69`. The arms agreed on the two rows
whose ends are observations and parted on the row whose end is a design change,
which is the row the claim predicts; the bullet is kept, and its effect is now
attributable to it rather than to the block round 15 measured.

Pre-registered outcome 4's antecedent fired too — the treated arm applied one
retirement template to all four rows, including the bare preference. Its harm
did not: the blind reader preferred that arm's register on exactly that row. The
outcome table let a keep and a retire fire together, which is a defect in the
instrument and is recorded as one. The general lesson is in memory: uniformity
of clause shape is not by itself the failure a reference may call it.

### `(instruction)` for iteration 20

1. Round 20 is the cleanup round by the every-fifth rule, and the block is now
   fully accounted for: preamble isolated (18), bullet isolated (19), everything
   else deleted. Nothing in `# Writing for other agents` is waiting on a
   measurement.
2. The `prompt-tests/general/` corpus is five cases for two prompt lines plus two
   unrelated rules. Run the ownership grep in the skill; then ask of each
   surviving case whether the condition naming it could ever be observed, which
   is a stricter test than the grep and the one `halve-the-runbook` — owned only
   by a paragraph about a deleted bullet — would have to pass. The user directed
   that fixture's shape, so deleting the *case* needs the user; deleting a
   condition that can never fire does not.
3. `.ralph/agent/*` was over the user's 6000-token ceiling for two rounds. The
   command is now in the contract. Run it before committing.
