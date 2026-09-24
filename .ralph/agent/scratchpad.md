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

**Real session logs under `~/.claude/projects/` carry the base rate a fixture
cannot.**

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

> **A condition in `sys_prompt/CLAUDE.md` names, in its own sentence, a case that
> exists and a comparison a later round could run.** *Retire this when an arm
> carrying the line does no better than one without* is the only actionable form.

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

> **A round opens no task row.** `tasks.jsonl` stays empty; the round's state is this
> file, `decisions.md` and the commit messages, which the ceiling already counts.
> DEC-039.

> **`decisions.md` carries only the half `sys_prompt/CLAUDE.md` does not** — what else
> was on the table, the framing bias, whether anyone independent looked, the revert
> sha. Claim, hypothesis and retirement condition are stated once, there.

> A retirement condition may name a **deleted probe** by its restore sha rather than a
> live case. `prompt-tests/runs/` is outside the ownership grep, so naming one pins no
> directory, and a condition then names where the observation was actually made.

> Operational rules for running, grading and deleting prompt tests live in
> `.claude/skills/prompt-tests/SKILL.md` and are not restated here.

## History — rounds 1–30, `9f6c03a0` → `3d5ddcdb`

Anything justifying a prompt line lives in `sys_prompt/CLAUDE.md` — read it before
touching the block. Everything else is in the commit messages. Shipped: `Say what
ends it` (11, upheld at 19), the self-consequence bullet (23), one duplicated
rationale cut out of it (25), the deletion of `pre_output.record`'s `NEVER reply to
user if uncertainties remain` (26, DEC-034), the deletion of the whole docs order at
`alan-default-next.md:15` (28, DEC-036). Deleted also: `Omit by default`, `Claim
less`, the help-surface cost paragraph. Nine candidate wordings failed, the last four
claim-handling and the ninth (30) a `rule added:` report bullet, saturated. Every
sentence still in the block has been measured alone. 29 kept the whole `# Writing for
other agents` block, refuting its own hypothesis that bullet 2 redirects growth into
prose; volume there was confounded with depth, and 30 removed that confound by
stating the load-bearing fact in the fixture — 13 tool calls an arm, and the volume
gap survived at 14 durable lines to 6. Unfalsified prose: 11 of 11 trees over three
rounds. Open and unmeasured: `# Error Propagation`'s `Silent retry` and `Partial
success` rows require retry counters and partial-failure lists against `# Coding`'s
minimum-complexity rule and its ban on one-time helpers; both blockquote-plus-table
duplications stand unmeasured. `scripts/check-prompt-upstream.py` cannot run here —
`/repos/claude-code-decompiled` is absent. DEC-037 – DEC-040.

## Iteration 31 — `3d5ddcdb` → (this round)

### Critique of 30

**C1 (fact — the reading that chose 30's direction is false).** Its pre-registration
says the user's specimen `e828eab7` "surfaced none of the three documentation
additions it made". The final message names all three: the `update-claude-code`
inventory row under `unexpected change:`, with an explicit revert offer; the
`session-analysis/CLAUDE.md` invoke-with-no-args rule in the body; the root-index row
in `## Summary`. Its `prompt_snapshot` carries `unexpected change:`. So the half of
the ratchet 30 called unserved is the half already firing in the wild, through the
one line no arm has ever run without — which is what this round ablates. Record 311
of the log.

**C2 (instrument — the condition points where the behaviour is measured absent).**
30's entry retires on `prompt-tests/general/hushed-rollcall`; `9504b5dc` measured
both arms there leaving the soliciting `CLAUDE.md` byte-identical. An arm cannot
"name the standing rules it wrote" where no arm writes one. The evidence was taken on
`amber-turnstile`, which the same round deleted.

**C3 (workflow — two standing rules collide, and the entry pays the ceiling in git's
currency).** Probes are deleted by their own round; conditions must name a live case;
so every probe-measured claim gets a condition naming a case where it was not
measured. `(contract)` below fixes it. Separately the entry carries the counts, arm
labels and fixture description the contract sends to git, and
`sys_prompt/CLAUDE.md` grew 36 lines for a round that shipped nothing.

### Milestone — ablate `unexpected change:`, the line no arm has run without

Chosen over a tenth say-less wording: nine have failed, and C1 shows the reporting
half works in the wild through this line. A shipped line whose justification was
written from arms that all carried it is the loop's own ratchet. Either outcome pays:
saturated deletes a line, load-bearing gives the entry its first falsifiable content
and tells later rounds that a report line does what nine say-less wordings could not.

Fixture: `amber-turnstile` restored from `9e66c94a` — the one genre where arms
demonstrably do write standing rules. Framing bias: it was built by 30 from the
shape of a report bullet, so it is the condition most favourable to reporting.

Pre-registration, readings and outcomes: the probe's `README.md`, and this round's
pre-registration commit.
