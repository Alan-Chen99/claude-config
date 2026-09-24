# writing-for-agents loop3 — scratchpad

The objective's sharpest clause is *things that do not require explicit human
approval to add, but require human intervention to remove*; the rest follows from
that ratchet. The user's 2026-09-24 followup makes *less documentation gets
written* the top priority. Carry **what retires this line** into every decision.

## Durable method, reusable across rounds

**The compression rule.** Cut in this order, stopping at the first load-bearing
class: a **claim**, a **restatement** (two wordings, nothing saying which governs),
a **duplicate of executable code**, a **trap** (keep). Deletion is the default.

**A line that names a consideration does not deliver the conclusion it argues
for.** It makes the consideration salient, and the agent argues it in whichever
direction the task favours.

**Categorical or it is not evidence, per reading rather than per table.** *Stated
bare or sourced* is readable at n=1; a count is a sample of an unmeasured spread.

**Test the lines already shipped.** A shipped line with a named, unmeasured harm
outranks any new candidate — inside the objective's scope only.

**The prompt is the whole stack, not one file.** `sys_prompt/alan-default-next.md`,
`output-styles/`, `conventions/documentation.md` (reached only via `doc-sync`,
`technical-writer`, `quality-reviewer`, `planner`) and
`src/claude_config/pre_output/record.py`, whose RULES string arrives in a tool
result before every response, all reach the session.

**Before writing a clause for a failure, re-run the failure in a second genre.**
If it disappears there, the target is the genre and not the wording.

## Standing `(contract)`

> An iteration may spend its milestone on any file in the stack, and may not spend
> a whole milestone on the prompt-test *instrument* unless it also runs at least
> one arm against `sys_prompt/alan-default-next.md`.

> A prompt edit's justification lands in `sys_prompt/CLAUDE.md` in the same commit,
> naming what would retire the line. Counts, arm labels, byte deltas, dates and
> fixture descriptions belong to git, not to that file. Each round either edits
> `sys_prompt/alan-default-next.md` or writes there what its own measurement showed
> that makes no edit the right call — as the first justification of a line that had
> none, naming the instrument defect a later round must fix, or else only replacing
> a paragraph, shorter.

> An edit that deletes or renames anything a document can point at, or withdraws a
> claim, sweeps the tree for citers in the same commit — `grep -rn --include='*.md'
> <name> .`, `.ralph/agent/` included — and the commit says which were left on
> purpose. **The round reads `git show --stat` of each commit against what it meant
> to commit and names anything else in the message.** Iteration 32 shipped 87 lines
> of stray shell trace into the repository root without noticing.

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

> **A line whose purpose is best-effort surfacing is not ablatable by a saturation
> reading**, because the requirement is a rate across sessions. `## Required notes`
> is such a line by the owner's stated intent; `sys_prompt/CLAUDE.md` carries it. Do
> not ablate one; price it by what it costs when it fires.

> **A round hands one line forward at most once**, and hands it forward **in the
> exact words a later round would run**. A second consecutive round on the same
> line decides it — ships an edit, deletes it, or records that the
> instrument cannot decide it and names the instrument that could. Three rounds
> ending in "one more reading" is the keep-by-default ratchet this objective is
> against, applied to the loop itself.

> **A condition in `sys_prompt/CLAUDE.md` names, in its own sentence, a runnable case
> and a comparison.** *Retire this when an arm carrying the line does no better than
> one without* is the only actionable form. A condition naming a fixture property
> no named case has is unobservable — check both directions.

> **Before a candidate wording is written, the round names one occurrence of the
> behaviour outside its own fixtures** — a real session log, a commit in this
> repo — or records that it looked and found none. **A session on this machine is
> read, not cited**: dispatch `session-analysis` in evidence mode. A claim about what
> an earlier round did or observed is checked against git before it is written —
> `git log --all -S'<line>'` for a prompt line, the result commit's own message for a
> result — and names the commit it checked. **A claim that the round's fixtures
> differ in some property is quoted from each fixture it compares**, deleted ones
> included.

> **The round ends under the user's `.ralph/agent/*` ceiling, with the number in
> its last commit message.** A round's own narrative is not what it spends the
> ceiling on: compress every earlier round's section to one paragraph first.
> `cat .ralph/agent/* | agent-tools count-tokens --file /dev/stdin` < 6000.
> `tasks.jsonl` stays empty and a task points here, never copies. DEC-039.

> **Ask the owner what a line is for before spending a round measuring it.** Two
> rounds were spent ablating `## Required notes` under a frame the owner's intent
> rules out; one question, answered in three minutes, settled it. One topic per
> loop; `skills/telegram-hitl`.

> Operational rules for running, grading and deleting prompt tests live in
> `.claude/skills/prompt-tests/SKILL.md` and are not restated here.

## History — rounds 1–32, `9f6c03a0` → `1497221c`

Anything justifying a prompt line lives in `sys_prompt/CLAUDE.md` — read it before
touching the block. Everything else is in the commit messages. Shipped: `Say what
ends it` (11), the self-consequence bullet (23), one duplicated rationale cut out of
it (25), the deletion of `pre_output.record`'s `NEVER reply to user if uncertainties
remain` (26, DEC-034), the deletion of the whole docs order at `alan-default-next.md:15`
(28, DEC-036). Deleted also: `Omit by default`, `Claim less`, the help-surface cost
paragraph. Nine candidate say-less wordings failed. 29 kept the whole `# Writing for
other agents` block, refuting its own hypothesis. 30 and 31 both spent a round on
`## Required notes` and shipped nothing; the owner settled it at 32 by saying what the
block is for. 32 built the hidden-docs tree 28 had named as the case its deletion was a
bet about and found the repair half saturated there too — all three arms repaired every
falsified statement — while a falsification-bounded wording cut unfalsified prose 44 → 6
lines against the bare arm, the first positive signal in ten candidates on the top
priority. Not shipped there: saturated first sentence, confounded at n=1 with that arm
skipping the review the others ran. Open and unmeasured: `# Error Propagation`'s
`Silent retry` and `Partial success` rows against `# Coding`'s minimum-complexity rule;
both blockquote-plus-table duplications. `scripts/check-prompt-upstream.py` cannot run
here — `/repos/claude-code-decompiled` is absent. DEC-037, DEC-042.

## Iteration 33 — `1497221c` → (pending)

### Critique of 32

**C1 (quality, verified).** `c8ff940d` committed `rep-skill-{1,2,3}.out` — 87 lines of
`set -x` trace from `claude.sh` — into the repository root, named in no commit message,
by a round whose message otherwise itemises every deletion and its restore command.
`git status` was clean afterwards, so the checklist passed on the letter while the round
whose subject is *things a human must intervene to remove* left three of them behind.
Deleted at `7fccd245`; contract clause added.

**C2 (fact, verified).** 32's handoff and its `sys_prompt/CLAUDE.md` entry both direct
the next round to measure "the bound alone", but the sentence they name — *That repair
is the documentation a change owes; what the change could newly explain is not* — opens
on an anaphor whose antecedent is the sentence 32 ruled out as saturated. No standalone
form of it exists, so a round following that instruction would have invented a wording
and attributed its result to a sentence never run. Contract clause added: a line is
handed forward in the words a later round would run.

**C3 (workflow, verified).** The contract already required naming one occurrence outside
the fixtures. 32 recorded the user's own specimen `e828eab7` as "a small change grew
documentation that only a human can remove" and marked the search as finding nothing —
while the log sat on this machine, readable. Read this round, it contradicts the frame
the candidate was measured under: two of its four durable additions were the literal ask
(*"and docuemnt it"*), one was commanded by a repo-local skill's own frontmatter
directive that no system-prompt line outranks, and the session's criterion at the moment
of writing was *"genuinely useful and unrecorded"* — usefulness alone. Contract clause
added: a session on this machine is read, not cited.
