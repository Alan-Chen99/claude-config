# writing-for-agents loop3 — scratchpad

The objective's sharpest clause is *things that do not require explicit human
approval to add, but require human intervention to remove*; the rest follows from
that ratchet. The user's 2026-09-24 followup makes *less documentation gets
written* the top priority. Carry **what retires this line** into every decision.

## Durable method, reusable across rounds

**The compression rule.** Cut in this order, stopping at the first class that is
load-bearing: a **claim** (only claims can be wrong), a **restatement** (two
wordings, nothing saying which governs), a **duplicate of executable code**
(replace with its name), a **trap** (what the reader gets wrong silently; keep).
Deletion is the default; each *keep* needs the argument.

**A line that names a consideration does not deliver the conclusion it argues
for.** It makes the consideration salient, and the agent argues it in whichever
direction the task favours.

**Categorical or it is not evidence, per reading rather than per table.** *Stated
bare or sourced* is readable at n=1; a count is a sample of an unmeasured spread.

**Test the lines already shipped.** A shipped line with a named, unmeasured harm
outranks any new candidate — inside the objective's scope only.

**When an instruction exists to compensate for a harness, fix the harness.**

**The prompt is the whole stack, not one file.** `sys_prompt/alan-default-next.md`,
`output-styles/`, `conventions/documentation.md` (reached only via `doc-sync`,
`technical-writer`, `quality-reviewer`, `planner`) and
`src/claude_config/pre_output/record.py`, whose RULES string arrives in a tool
result before every response, all reach the session.

**Before writing a clause for a failure, re-run the failure in a second genre.**
If it disappears there, the target is the genre and not the wording.

**A fixture written from the shape of the line tests the wording, not the world.**
Real session logs under `~/.claude/projects/` carry the base rate a fixture
cannot.

## Standing `(contract)`

> An iteration may spend its milestone on any file in the stack, and may not spend
> a whole milestone on the prompt-test *instrument* unless it also runs at least
> one arm against `sys_prompt/alan-default-next.md`.

> A prompt edit's justification lands in `sys_prompt/CLAUDE.md`, naming what would
> retire the line, in the same commit as the edit. Counts, arm labels, byte
> deltas, dates and fixture descriptions belong to git, not to that file.

> An edit that deletes or renames anything a document can point at, or withdraws a
> claim, sweeps the tree for citers in the same commit — `grep -rn --include='*.md'
> <name> .`, `.ralph/agent/` included — and the commit says which were left on
> purpose.

> Each round either edits `sys_prompt/alan-default-next.md`, or writes into
> `sys_prompt/CLAUDE.md` what its own measurement showed that makes no edit the
> right call. A round that ships no prompt edit may add a paragraph there only as
> the first justification of a line that had none, naming the instrument defect a
> later round must fix; otherwise it may only replace a paragraph, shorter.

> **Run the case-ownership grep in both directions before leaving.** A paragraph in
> `sys_prompt/CLAUDE.md` naming no case, or naming a fixture property no case has,
> states nothing a later round can observe; it is deleted or given its case by the
> round that finds it. The skill states the rule; rounds have only ever run the
> direction that deletes fixtures.

> Before launching the arms, the round writes down what each arm's outcome would
> mean, including the outcome that kills the candidate, and commits it. **Outcomes
> are keyed to the blind reader's own questions**, and where the trees of one arm
> disagree on an axis that axis is spread, not effect. A reading composed after the
> arms are in is not admissible.

> **A round's decisive reading is made by a reader that is not the round**, told
> neither what is being tested nor which arm is which.

> **A null is reported as saturated, not as a finding, when the untreated arm
> already does the thing** — and where the line under test is a shipped one, a
> saturated baseline is a reason to delete it. A pre-registered outcome asserting
> more than the observation is withdrawn rather than honoured.

> **A condition written into `sys_prompt/CLAUDE.md` names, in its own sentence, a
> case that exists in the tree and a comparison a later round could run** — *retire
> this when an arm carrying the line does no better than one without* is the only
> form that is actionable.

> **Before a candidate wording is written, the round names one occurrence of the
> behaviour outside its own fixtures** — a real session log, a commit in this
> repo — or records that it looked and found none.

> **A claim that the round's fixtures differ in some property is quoted from each
> fixture it compares** — the whole comparison, deleted ones included.

> **The round ends under the user's `.ralph/agent/*` ceiling, with the number in
> its last commit message.** A round's own narrative is not what it spends the
> ceiling on: compress every earlier round's section to one paragraph first.
> `cat .ralph/agent/* | agent-tools count-tokens --file /dev/stdin` < 6000.
> `tasks.jsonl` counts toward it: a task points here, never copies.

> **A claim about what an earlier round did or observed is checked against git
> before it is written** — `git log --all -S'<line>'` for a prompt line, the
> result commit's own message for a result — and names the commit it checked.

> Operational rules for running, grading and deleting prompt tests live in
> `.claude/skills/prompt-tests/SKILL.md` and are not restated here.

## History — rounds 1–25, `9f6c03a0` → `00396475`

Anything justifying a prompt line lives in `sys_prompt/CLAUDE.md` — read it before
touching the block. Everything else is in the commit messages. Shipped: `Say what
ends it` (11, upheld at 19), the self-consequence bullet (23), one duplicated
rationale cut out of it (25). Deleted: `Omit by default`, `Claim less`, the
help-surface cost paragraph. Eight candidate wordings failed, the last four all
claim-handling. Round 10 voided every arm stored before 2026-09-22. Every sentence
still in the block has been measured alone.

## Iteration 26 — `00396475` → `d8b2ba5c`

Withdrew 25's instruction 1: git showed iteration 19 had already run the case it
said no round had run. Shipped the deletion of `pre_output.record`'s `NEVER reply to user if
uncertainties remain` on three runs of `retirement-policy`; DEC-034 carries the
reading and its limits. Transferable: a rule arriving in a tool result acts only
on what follows the call, and every arm replied with residual doubt listed anyway.

## Iteration 27 — `d8b2ba5c` → `59bb9965`

Withdrew 26's live-case attribution — record 107 named both doc homes before 108
read `conventions/documentation.md`, which nothing auto-loads. Milestone:
`alan-default-next.md:15`'s third clause, shipped and never justified. Four runs,
two arms, no prompt edit: a blind reader grouped all four trees on whether the
*first* listing showed the `.md` files, a split cutting across the arms, and the
arm *without* the clause is the one that grepped exactly the root `CLAUDE.md` the
clause names. DEC-035 records the line untested and names the instrument fix.
Arm-independent, on the top priority: a doc repair is a paragraph **rewrite** that
drops inherited rationale, and it **appends** prose the change had not falsified.

## Iteration 28 — `59bb9965` → (pending)

### Critique of 27

**C1 (workflow — the loop's own ratchet).** A round that shipped no prompt edit
added 36 lines to `sys_prompt/CLAUDE.md`, concluding in its own text that the line
is untested and that its two real findings do not belong in that file. The probe
those lines rest on was deleted in the same commit, so the paragraph names no case
and its stated condition — *a fixture whose doc files are named in the auto-loaded
root `CLAUDE.md`* — names a fixture property no case has. The skill already calls
that a deletion candidate; no round had ever run the grep in that direction.
Contract amended above. The amendment permitting the addition was written by 27
in the commit that used it.

**C2 (workflow — priority).** 27's only reproducible, arm-independent observation
was the growth mechanism the user's followup calls the top priority, and it
disposed of it in four words — *neither mechanism lives in `sys_prompt/`* — with
no test and no argument, then pointed 28 at search breadth, which serves doc
correctness instead. `# Writing for other agents` ships two bullets aimed at what goes
into a lasting document; neither was varied in those runs, so nothing measured
supports the claim that the prompt cannot reach the mechanism.

**C3 (measurement).** Both of 27's pre-registered outcomes "partly fired", so
neither was honoured and four runs decided nothing. The defect is the pre-registration: outcomes were
written about the trees while the decisive reading turned out to be a blind
reader's grouping nobody had named. 28 pre-registers the reader's questions and
derives the outcomes from the answers.

### Milestone

The whole of `alan-default-next.md:15` on trial for deletion — not the third
clause alone, which subsumes 27's instruction 1, since the breadth sentence it
names is the second. The instrument defect C1 names is fixed first: the fixture's
auto-loaded `CLAUDE.md` indexes every doc file, so no arm can miss them.
Pre-registration and fixture: `prompt-tests/runs/option-and-encoding/README.md`.

### `(instruction)` for iteration 29

1. Unspent from 26, twice deferred: read `# Epistemic Integrity`, `# Error
   Propagation` and `## Required notes` as prose before measuring any of them.
2. `tasks.jsonl` grows ~190 tokens a round against the ceiling, with no prune
   command. Round 30's cleanup solves that or the ceiling eats the scratchpad.
