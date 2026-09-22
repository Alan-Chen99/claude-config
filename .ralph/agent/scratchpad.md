# writing-for-agents loop3 — scratchpad

The objective's sharpest clause is *things that do not require explicit human
approval to add, but require human intervention to remove*; the rest follows from
that ratchet. Carry **what retires this line** into every decision.

## Durable method, reusable across rounds

**The compression rule.** Cut in this order, stopping at the first class that is
load-bearing: a **claim** (only claims can be wrong), a **restatement** (two
wordings, nothing saying which governs), a **duplicate of executable code**
(replace with its name), a **trap** (what the reader gets wrong silently; keep).
Deletion is the default; each *keep* needs the argument.

**A line that names a consideration does not deliver the conclusion it argues
for.** It makes the consideration salient, and the agent argues it in whichever
direction the task favours. Measured twice on `Omit by default`'s reach wording.

**A retirement condition names a comparison, not an observation** — *retire this
when an arm carrying the line does no better than one without* is the only form
a later round can act on.

**Buy resolution inside the run.** At n=1 one opportunity yields a coin flip;
several that *differ in character* yield the policy the agent applied.

**Categorical or it is not evidence, per reading rather than per table.** *Stated
bare or sourced* is readable at n=1; a count is a sample of an unmeasured spread.
Hardest to hold where the excluded number is the one you want.

**Test the lines already shipped.** A shipped line with a named, unmeasured harm
outranks any new candidate.

**When an instruction exists to compensate for a harness, fix the harness.** An
`(instruction)` telling a later round to remember something is a rule nothing
approves and only a human retires.

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

> **No claim in `sys_prompt/CLAUDE.md` may be a run narrative.** It carries the
> semantic claim, the hypothesis for it, and the retirement condition. Counts, arm
> labels, byte deltas, dates and fixture descriptions belong to git.

> **A round's decisive reading is made by a reader that is not the round**, told
> neither what is being tested nor which arm is which. Its answer is the result,
> not a check on one already written.

> **A null is reported as saturated, not as a finding, when the untreated arm
> already does the thing** — and where the line under test is a shipped one, a
> saturated baseline is a reason to delete it, not a reason to withhold judgement.
> A pre-registered outcome asserting more than that is withdrawn rather than
> honoured. *(18, 19)*

> **An `(instruction)` asserting that work is undone states the command that
> shows it.**

> **The round ends under the user's `.ralph/agent/*` ceiling, with the number in
> its last commit message** — not in a file here, where writing it changes it.
> `cat .ralph/agent/* | agent-tools count-tokens --file /dev/stdin` < 6000.

> Operational rules for running, grading and deleting prompt tests live in
> `.claude/skills/prompt-tests/SKILL.md` and are not restated here.

## History — rounds 1–20, `9f6c03a0` → `a9fc0fc6`

Anything justifying a prompt line lives in `sys_prompt/CLAUDE.md` — the durable
home, and the file to read before touching the block. Everything else is in the
commit messages. Shipped: `Say what ends it` (9). Deleted: `Omit by default`
(13, 17), `Claim less` (4, 14). Eight candidate wordings failed (3–8, 12, 14, 16,
18, 20), the last three all claim-handling. The corpus is bound to the prompt by
one grep; eleven of fifteen cases deleted (15). Round 10 fixed a nine-round
harness contamination and voided every arm stored before 2026-09-22. Every
sentence still in the block has been measured alone (18, 19).

## Iteration 21 — `a9fc0fc6` → `0a2ade7e` + this commit

### Critique of prior iterations

**C1 (workflow — 20's instruction 2 sends the next round outside the objective).**
It ranks the subagent bullet's unverified override clause above any new candidate.
That bullet governs neither documentation nor agent-to-agent text, so measuring it
advances no bullet of the objective; and the objective's ratchet bullet says *your
job is not to clean this, but to ensure there are less new things of this form* —
removing an existing unmeasured clause is the cleaning the user excluded. The
heuristic behind it (*a shipped line with a named unmeasured harm outranks any new
candidate*) is sound, but it was applied outside the block without re-checking
scope. Instruction 2 is overridden. The heuristic is kept and applied **inside**
scope, which is what this round does.

**C2 (workflow — two rules 20 shipped in one round pull against each other).**
*Provenance does not own a case* and *no claim in `sys_prompt/CLAUDE.md` may be a
run narrative* were both added by 20. Three of the five corpus matches were then
narrative sentences, with the owning sentence pointing back at them as *on that
case* — so obeying the second rule deletes the first rule's only evidence and the
grep orders three fixtures destroyed. 20 never re-ran its own grep after writing
them. Fixed: every owning sentence now carries the path; the narrative is gone;
the skill states the requirement.

**C3 (fact — a hypothesis generalised past the two wordings that produced it).**
`sys_prompt/CLAUDE.md` asserted *no wording can make a passing sentence salient*
from two candidates of one shape — both mark or redirect a doubt presumed already
present. Meanwhile the prompt itself supplies a mandatory destination for exactly
that content outside the artifact: `pre_output.record`'s `uncertainties`,
*unresolved observations, unverified assumptions, unconfirmed data*, recorded every
turn. No round has measured it. A claim about all wordings, written while a shipped
line is a live candidate cause, is not supported.

### Why this milestone

C3 names the one untested surface that is inside the objective, is a **shipped**
line rather than a new candidate, and whose repair is a deletion — so it serves the
ratchet bullet instead of working against it. It also explains three nulls at once:
if the doubt is being filed in a tool call every turn, a bullet telling the agent to
put it in the file competes with an IMPORTANT/NO EXCEPTIONS gate and loses.

The probe is one arm, because the decisive reading is available inside a single
session: does the `uncertainties` array name the same premise the delivered document
asserts flat? Only if it does is the two-arm removal test worth running.

### The round's work and result

Cleanup half, `5dff4c0f`: every case-owning sentence in `sys_prompt/CLAUDE.md`
now carries the path, so the grep no longer rests on narrative another rule
forbids; a citation to a directory not in this worktree goes with it.
Measurement half: pre-registration `19a6af3f`, result and claim `15d439ee`.

**Outcome 1, with its interpretation withdrawn.** The session's own
`uncertainties` named three facts the working directory cannot settle. Two
reached the document as pre-flight checks; the third was asserted flat inside a
sentence explaining how a step works, and the session reported all three as
documented. So the sink is not diverting doubts wholesale — the removal test the
outcome proposed does not follow — and *no wording can reach a passing sentence*
is withdrawn, since the doubt was present, written down and believed delivered.
What separates the three is the sentence's job: two gate an act the reader
performs, the third describes. The blind reader, told nothing, independently
named that flat sentence as the thing that would stop a successor.

The probe is promoted rather than deleted, which is the first time the deletion
rule has been overridden: the condition needs a document with both an
instructing and an explaining part leaning on unsettleable facts, and rebuilding
that costs more than the directory does. Its `reference-solution.md` states what
the fixture settles and what it does not, and no verdict on either.

### `(contract)` amendment

> **A condition written into `sys_prompt/CLAUDE.md` names, in its own sentence,
> either a case that exists in the tree or an observation any run would show.**
> Replaces 19's ownership rule in the condition→case direction. 20 wrote a
> condition whose fixture nobody had built; 20 also left three conditions
> pointing at their case as *on that case*, which its own no-narrative rule
> would have silently unowned. Both are the same defect.

### `(instruction)` for iteration 22

1. The measured target is now *a premise inside an explanatory sentence*, not
   *a premise nobody flagged*. Eight wordings failed against the older target;
   none has been written against this one. A ninth is admissible, and
   `prompt-tests/general/maintainer-briefing` is the fixture that reads it —
   both arms, categorical, per premise, decided blind.
2. Before writing that wording, note what the successful half did unaided: the
   two doubts that reached the file did so as *things the reader must confirm
   before acting*. A wording that asks the explaining half to borrow that
   shape is closer to the measured mechanism than one asking for a hedge.
3. `uncertainties` is not closed as a subject, only as this round's explanation.
   It carries content that belongs to the reader of the file and reaches only
   the user; what no round has measured is whether the agent would have found
   the third premise at all without the field asking for it.
4. 20's instruction 2 (the subagent override clause) is overridden; see C1. Do
   not reinstate it without arguing that the bullet is inside the objective.
