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

**A retirement condition names a comparison, not an observation** — *retire this
when an arm carrying the line does no better than one without* is the only form
a later round can act on.

**Buy resolution inside the run.** At n=1 one opportunity yields a coin flip;
several that *differ in character* yield the policy the agent applied.

**Categorical or it is not evidence, per reading rather than per table.** *Stated
bare or sourced* is readable at n=1; a count is a sample of an unmeasured spread.

**Test the lines already shipped.** A shipped line with a named, unmeasured harm
outranks any new candidate — inside the objective's scope only.

**When an instruction exists to compensate for a harness, fix the harness.**

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

> An iteration may not spend its whole milestone on the prompt-test instrument
> unless that iteration also runs at least one arm against
> `sys_prompt/alan-default-next.md`.

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
> composed after the arms are in is not admissible. Any claim that a rule
> delivered through a tool result caused a behaviour states the tool-call index of
> both.

> **A round's decisive reading is made by a reader that is not the round**, told
> neither what is being tested nor which arm is which.

> **A null is reported as saturated, not as a finding, when the untreated arm
> already does the thing** — and where the line under test is a shipped one, a
> saturated baseline is a reason to delete it. A pre-registered outcome asserting
> more than the observation is withdrawn rather than honoured.

> **A condition written into `sys_prompt/CLAUDE.md` names, in its own sentence,
> either a case that exists in the tree or an observation any run would show.**

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

> **A round may spend its milestone on any file in the stack above**, justified in
> `sys_prompt/CLAUDE.md` as always. The standing ban is on spending a whole
> milestone on the prompt-test *instrument*, which none of those files is.

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

## Iteration 26 — `00396475` → `291d3c55` (+ this commit)

### Critique of 25

**C1 (fact — instruction 1 rests on a claim about the loop that git falsifies).**
25 wrote that `Say what ends it` "has gone three rounds without an observed exit
priced in any arm" and that "no round has run [`retirement-policy`] since the
bullet shipped". The bullet shipped at `52f519de` (05:13); iteration 19 ran that
case against it four hours later (`b71737f7`, `4eae4b69`): the arms part on the
row whose end is a design change, and a blind reader preferred the treated arm on
the register row. The condition did not fire and `sys_prompt/CLAUDE.md` still
carries that reading. Instruction 1 withdrawn, nothing replaces it. Same failure
class 25 caught in 24, one level up — 25 required fixture-property claims to be
quoted, and then wrote an unchecked claim about run history. Contract amended.

**C2 (workflow — the user handed a live case and three rounds did not open it).**
The followup names session `e828eab7` and its two commits as an instance of the
top-priority failure. 23–25 ran fixture probes on the block instead. The loop's
own memory says a log finds the mechanism a fixture cannot. Opened here.

**C3 (workflow — 25 rounds optimised one file; the stack is larger).** See the
durable-method line added above. The live case attributes growth to two members
of the stack that no round has measured: `conventions/documentation.md`'s
*Duplication is acceptable; the maintenance burden is the cost of locality*, read
at record-index 108 and followed at 112 by the decision to give one fact two
homes; and `pre_output.record`'s *NEVER reply to user if uncertainties remain*.

### The live case, read

Detail and tool-call indices are in `858a2ab5`. In one line: a one-symlink task
produced ~20 lines of durable text across four files plus a second commit
refining two of them, and the only part attributable by quotation is the
`pre_output.record` reminder, which the session answered by settling its cheapest
doubt, dropping another unresolved, and writing the answer into two documents —
while naming the real fix under `possible-next-steps` twice and leaving it undone.

### Why this milestone

The user's top priority is that less documentation gets written; the strongest
evidence available is the live case, and the only growth in it attributable by
quotation is this line. It is shipped, unmeasured, NEVER-force, delivered before
every response, and lives in a file nobody reads — the objective's own target
shape. The durable method already ranks a shipped line with a named unmeasured
harm above any new candidate.

### The round's work and result

Two commits. `b2ecb31d` fixes the harness the probe exposed: `agent-tools claude`
wires the binary to the checkout and never asserted the Python half, so this
worktree's venv served `/repos/claude-config/src` and the first attempt at arm b
would have been a silent null. `291d3c55` ships the deletion on outcome 2 — three
runs, readings and limits in the commit and in `sys_prompt/CLAUDE.md`.

The result that matters beyond this line: **every arm disproved the task's own
account of an incident without being told to, and every arm replied with residual
doubt still listed, including one tool call after receiving a rule that says
NEVER.** A tool-result rule arriving after the work is done cannot do anything;
when it arrives early enough to act, what it adds is writing.

### `(instruction)` for iteration 27

1. The same three-wordings defect is one level up and unmeasured: `# Epistemic
   Integrity`, `# Error Propagation` and `## Required notes` in
   `sys_prompt/alan-default-next.md` all tell the agent to surface what it could
   not settle. Read the block as prose before measuring any of it — 25 found a
   restatement that way and no per-line measurement could have.
2. `conventions/documentation.md` line 11 says *Duplication is acceptable; the
   maintenance burden is the cost of locality*. The live case read it at
   record-index 108 and gave one fact two homes at 112. It is auto-pulled by any
   doc-writing task, is outside `sys_prompt/`, and no round has measured it. This
   is the strongest remaining candidate for *less documentation gets written*.
3. Do not re-open `Say what ends it`. 19 measured it in isolation on its own case
   and the condition did not fire; C1 above.
