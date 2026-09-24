# writing-for-agents loop3 — scratchpad

The objective's sharpest clause is *things that do not require explicit human
approval to add, but require human intervention to remove*; the rest follows from
that ratchet. The user's 2026-09-24 followup makes *less documentation gets
written* the top priority and hands a live case for it. Carry **what retires this
line** into every decision.

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

**Attribution runs on the decision's index, not the read's.** A file read after
the decision is already formed in the transcript explains nothing; and a live
case's growth is charged to the prompt only after reading the request that
started it.

**The prompt is the whole stack, not one file.** `sys_prompt/alan-default-next.md`,
`output-styles/`, `conventions/documentation.md` (pulled in by any doc-writing
task) and `src/claude_config/pre_output/record.py` — whose RULES string is
delivered in a tool result before every response, at NEVER force — all reach the
session. 25 rounds measured the first only.

**Before writing a clause for a failure, re-run the failure in a second genre.**
If it disappears there, the target is the genre and not the wording.

**A fixture written from the shape of the line tests the wording, not the world.**
Real session logs under `~/.claude/projects/` carry the base rate a fixture
cannot. One extraction of one live session found the mechanism three fixture
rounds had missed (22).

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
> right call. A round that ships no prompt edit may not add a paragraph there; it
> may replace one, and the replacement is shorter.

> Before launching the arms, the round writes down what each arm's outcome would
> mean, including the outcome that kills the candidate, and commits it. A reading
> composed after the arms are in is not admissible.

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
> fixture it compares, in the commit that first states it.** The whole comparison
> is named, deleted ones included (`git show <sha>:<path>`).

> **The round ends under the user's `.ralph/agent/*` ceiling, with the number in
> its last commit message.** A round's own narrative is not what it spends the
> ceiling on: compress every earlier round's section to one paragraph first.
> `cat .ralph/agent/* | agent-tools count-tokens --file /dev/stdin` < 6000.
> `tasks.jsonl` counts toward it: a task points here, never copies.

> **A claim about what an earlier round did or observed is checked against git
> before it is written** — `git log --all -S'<line>'` for a prompt line, the
> result commit's own message for a result — and names the commit it checked.
> 25's rule covers claims about fixtures; this covers claims about the loop.

> Operational rules for running, grading and deleting prompt tests live in
> `.claude/skills/prompt-tests/SKILL.md` and are not restated here.

## History — rounds 1–25, `9f6c03a0` → `00396475`

Anything justifying a prompt line lives in `sys_prompt/CLAUDE.md` — the durable
home, and the file to read before touching the block. Everything else is in the
commit messages. Shipped: `Say what ends it` (11, isolated and upheld at 19), the
self-consequence bullet (23), one duplicated rationale cut out of it (25).
Deleted: `Omit by default`, `Claim less`, the help-surface cost paragraph. Eight
candidate wordings failed, the last four all claim-handling. Round 10 voided
every arm stored before 2026-09-22. Every sentence still in the block has been
measured alone.

## Iteration 26 — `00396475` → `d8b2ba5c`

Withdrew 25's instruction 1: git showed iteration 19 had already run the case it
said no round had run. Opened the live case the user handed, `e828eab7`. Fixed
`agent-tools claude` to assert the venv's `claude_config` comes from this
checkout — without it arm b was a silent null. Shipped the deletion of
`pre_output.record`'s `NEVER reply to user if uncertainties remain` on three runs
of `retirement-policy`; DEC-034 carries the reading and its limits. Transferable
result: a rule arriving in a tool result acts only on what follows the call, and
every arm replied with residual doubt still listed anyway.

## Iteration 27 — `d8b2ba5c` → (this commit)

### Critique of 26

**C1 (fact — the live case's attribution fails on its own indices).** 26 wrote
that `conventions/documentation.md`'s *Duplication is acceptable* was "read at
record-index 108 and followed at 112 by the decision to give one fact two homes".
The log says otherwise. At 107, *before* the read, the agent had already named
both homes ("I might need to create one since the root doc says details should
live in each directory's own file" … "also consider adding a line to
`skills/session-analysis/CLAUDE.md`"), and 108's stated purpose was "how table
rows are formatted". At 112 the second home is justified by audience — "that file
gets read when someone's actively working on the skill" — not by duplication
being acceptable. The attribution is withdrawn and with it instruction 2's claim
that line 11 is the strongest remaining candidate.

**C2 (fact).** 26 called that file "auto-pulled by any doc-writing task". It is
referenced only by `skills/doc-sync/SKILL.md`, `agents/technical-writer.md`,
`agents/quality-reviewer.md` and `skills/planner/resources/plan-format.md`, none
auto-loaded; in the live case the agent reached it with a hand-written `sed`.

**C3 (workflow — no round read the request the live case started from).** User
prompt at record 8 ends "and docuemnt it". 26's write-up frames ~20 lines of
durable text as unrequested growth from a one-symlink task. Documentation was
requested; what the stack can be charged with is spread and volume. Durable-method
line added above.

**C4 (fact — the stack's most direct doc-growth order went unread for 26
rounds).** `sys_prompt/alan-default-next.md:15`, third clause: *After making a new
file **or making edits**, check if project CLAUDE.md needs an update.* It is
strictly wider than the wording it was forked from
(`output-styles/alan-default-next.md:70`: *When you add a new file, update project
CLAUDE.md*). `sys_prompt/CLAUDE.md` has no section on `# Doing tasks`, so the
widening is unjustified and unmeasured. Milestone.
