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

## History — rounds 1–27, `9f6c03a0` → `59bb9965`

Anything justifying a prompt line lives in `sys_prompt/CLAUDE.md` — read it before
touching the block. Everything else is in the commit messages. Shipped: `Say what
ends it` (11, upheld at 19), the self-consequence bullet (23), one duplicated
rationale cut out of it (25), the deletion of `pre_output.record`'s `NEVER reply to
user if uncertainties remain` (26, DEC-034). Deleted: `Omit by default`, `Claim
less`, the help-surface cost paragraph. Eight candidate wordings failed, the last
four all claim-handling. Round 10 voided every arm stored before 2026-09-22. Every
sentence still in the block has been measured alone. 27 spent four runs on
`alan-default-next.md:15` and decided nothing: a blind reader grouped its trees on
whether the session's first listing showed the `.md` files, a split cutting across
the arms.

## Iteration 28 — `59bb9965` → `adb80213`

Put the whole docs order at `alan-default-next.md:15` on trial against a fixture
whose auto-loaded `CLAUDE.md` indexes its own documents, so 27's dominant variable
was gone. Four runs, two arms, pre-registered at `901be8f4`. **Shipped the
deletion**, saturated: both arms rewrote all three documents, followed a data-file
rename through them, and three of four added a `CLAUDE.md` row for a file they had
created — one an arm with no docs instruction at all. DEC-036. Arm-independent and
on the user's top priority: 4 of 4 trees added prose the change had not falsified,
after 3 of 3 in 27, in a second genre — and **not one tree wrote a standing rule**,
including into the `## Conventions` heading the fixture solicits one from. The
probe was promoted to `prompt-tests/general/option-and-encoding`.

## Iteration 29 — `2894f884` → ...

### Critique of 28

**C1 (workflow — the ratchet, inside the loop's own corpus).** 28 promoted its
probe into `prompt-tests/general/` with three-quarters of a case: a
`reference-solution.md`, three foci no run has been read under, and no stored
artifacts. The skill defines a case as reference, grader per arm, foci and stored
runs, and the reason it gives for keeping one is artifact-against-artifact
comparability — which a case holding no artifacts cannot offer. The corpus grew by
a directory only a human removes, the form the objective names. Its stated reason,
*the restoration condition has to name a case that exists*, is circular: the
condition was written in the same commit. This round runs the case whole.

**C2 (workflow — priority; the charge 28 laid on 27).** 28's scratchpad states
*that makes the repair-as-rewrite genre, not any prompt clause, the target for the
user’s top priority*, from four arms all carrying `# Writing for other agents`
intact. The clause aimed at what goes into a lasting document was never varied, so
nothing measured supports *not any prompt clause*, and a later round reading the
scratchpad alone stops looking in the prompt. 28’s own instruction 1 names the fix.

**C3 (measurement — the instrument was blind to the mechanism).** The decisive
blind reading was taken on delivered **trees**; the skill’s blind comparison holds
both **sessions**. A tree cannot show an addition considered and declined, which is
this block’s characteristic effect in the loop’s own prior readings — DEC-033’s
limit is exactly that. So *not one tree wrote a standing rule* was measured with an
instrument that cannot separate suppression from absence. This round’s blind reader
gets the sessions.

### Milestone

The whole of `# Writing for other agents` on trial, on the promoted case, at n=1 an
arm. Live hypothesis: bullet 2’s remedy clause *Put it with the change instead* is
what the 7-of-7 growth obeys — the additions were rationale prose inside the
repaired documents and no standing rules, which is the shape that bullet asks for.
An arm without the block separates *the block suppresses rules* from *the block
redirects rules into prose*. Pre-registration and outcomes: this commit.
