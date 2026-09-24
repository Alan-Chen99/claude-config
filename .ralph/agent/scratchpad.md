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

> **A line whose purpose is best-effort surfacing is not ablatable by a saturation
> reading.** The owner's intent for `## Required notes` (2026-09-24): the bullets
> exist so a recurring problem *eventually* reaches the user across many sessions,
> and being surfaced *sometimes* is the whole requirement. One untreated session
> that surfaces the same item refutes nothing about a per-occurrence rate. Do not
> ablate such a line; price it by what it costs when it fires.

> **A round hands one line forward at most once.** A second consecutive round on
> the same line decides it — ships an edit, deletes it, or records that the
> instrument cannot decide it and names the instrument that could. Three rounds
> ending in "one more reading" is the keep-by-default ratchet this objective is
> against, applied to the loop itself.

> **A condition in `sys_prompt/CLAUDE.md` names, in its own sentence, a runnable case
> and a comparison.** *Retire this when an arm carrying the line does no better than
> one without* is the only actionable form. A condition naming a fixture property
> no named case has is unobservable — check both directions.

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

> **Ask the owner what a line is for before spending a round measuring it.** Two
> rounds were spent ablating `## Required notes` under a frame the owner's intent
> rules out; one question, answered in three minutes, settled it. One topic per
> loop; `skills/telegram-hitl`.

> Operational rules for running, grading and deleting prompt tests live in
> `.claude/skills/prompt-tests/SKILL.md` and are not restated here.

## History — rounds 1–31, `9f6c03a0` → `b3dc93b6`

Anything justifying a prompt line lives in `sys_prompt/CLAUDE.md` — read it before
touching the block. Everything else is in the commit messages. Shipped: `Say what
ends it` (11), the self-consequence bullet (23), one duplicated rationale cut out of
it (25), the deletion of `pre_output.record`'s `NEVER reply to user if uncertainties
remain` (26, DEC-034), the deletion of the whole docs order at `alan-default-next.md:15`
(28, DEC-036). Deleted also: `Omit by default`, `Claim less`, the help-surface cost
paragraph. Nine candidate say-less wordings failed. 29 kept the whole `# Writing for
other agents` block, refuting its own hypothesis. 30 and 31 both spent a round on
`## Required notes` and shipped nothing; 31's ablation of `unexpected change:` found
both arms writing and naming the same standing rules, refuting 30's stated mechanism.
Open and unmeasured: `# Error Propagation`'s `Silent retry` and `Partial success` rows
against `# Coding`'s minimum-complexity rule; both blockquote-plus-table duplications.
`scripts/check-prompt-upstream.py` cannot run here — `/repos/claude-code-decompiled`
is absent. DEC-037 – DEC-041.

## Iteration 32 — `b3472db2` → (see close)

### Critique of 28–31

**C1 (instrument, verified).** 28's restore condition for the docs order names
`prompt-tests/general/option-and-encoding`, whose fixture `CLAUDE.md` carries a
`## Files` table indexing every document — while `adb80213`'s own limits paragraph
says the saturation holds *because* the tree indexes its documents and that the
untested case is "a tree that both hides its documents and is repaired by an agent
that searches narrowly, which is the case this deletion is a bet about". The
condition therefore cannot be observed where it points, and four rounds passed with
that unnoticed. The prompt-tests skill already names this defect class; nobody ran
its second direction.

**C2 (workflow, verified).** `git log --oneline -- sys_prompt/alan-default-next.md`:
the last prompt edit is `adb80213`, iteration 28. Rounds 29, 30 and 31 shipped none,
and all three spent their milestone in one neighbourhood — the `# Writing for other
agents` block, then a `## Required notes` bullet twice — each ending by handing the
same line forward for one more reading. That is the objective's own ratchet applied
to the loop: a shipped line survives because deciding it is always deferrable.
Contract clause added.

**C3 (fact, settled by the owner).** 30 and 31 both decided a `## Required notes`
bullet by asking whether an untreated arm does the same thing once. Asked on the
channel, the owner said the block is **best effort** — "the important is they are
sometimes surfaced", so a recurring problem eventually reaches them. The requirement
is a rate across sessions, and no single-session saturation reading can bear on it.
Both rounds' frames were undecidable whatever the arms showed, and neither round
asked the one question that settles it. The entry in `sys_prompt/CLAUDE.md` is
rewritten around the owner's intent and no longer waits on a measurement.

### Milestone and result — the repair half is dead, the bound is the live half

**Milestone chosen** over 31's handoff: the owner's newest followup names the docs
order directly, user instruction outranks a prior iteration's `(instruction)`, and 28's
own limit names the same untested tree. Three arms on a tree that hides its documents
— `CLAUDE.md` with conventions and no index, `docs/` reachable only by looking, a task
naming no document — with nine statements across four files falsified by the changes
asked for. a0 no bullet, a1 the deleted line verbatim, a2 a bound: *That repair is the
documentation a change owes; what the change could newly explain is not.*

**Every arm repaired or deleted every falsified statement, a0 included.** O1 fired, in
the genre 28 called the case its deletion was a bet about. The repair half of any docs
order is saturated in two genres now, and the owner's staleness worry is not realised:
a0's reasoning listed the four documents it had falsified before writing any code.

**What separated them is the half nobody had written.** Unfalsified prose 44 lines
(a0), 27 (a1), 6 (a2); standing instruction-sentences 4, 4, 2. First positive signal
in ten candidates on the top priority. a2's reasoning shows the mechanism, not just
the artifact: the falsified set enumerated as a list, discoveries routed to the reply,
and **not one narrowing decision gave a documentation-scope reason** — every one was
implementation scope or what the user had asked for.

**Not shipped.** a2's first sentence is the saturated half, and shipping a saturated
sentence to carry an effective one is the duplication the file's own step 2 forbids.
Its second half is confounded at n=1: a2 also declined the review both other arms ran
and shipped the one live defect, an uncaught `OverflowError`. The quoted reasoning does
not connect them, which weakens the confound without removing it.

`prompt-tests/general/option-and-encoding` went unowned when that entry was rewritten
and is deleted; `b01c312e` restores it. DEC-042.

### `(instruction)` for iteration 33

1. **Measure the bound alone**, with no repair clause in front of it, against a bare
   arm. Restore the tree with `git checkout 37a6b901 -- prompt-tests/runs/copper-lantern`,
   or build a second genre. Fix investigation depth by construction — state the
   load-bearing fact in the fixture (`mem-1790442000-31ac`) — so volume cannot ride on
   how much each arm found out, and pre-register the code-review decision as a reading,
   since that is what the confound rode on here.
2. **Do not ablate a `## Required notes` bullet.** Owner intent settles it; the entry in
   `sys_prompt/CLAUDE.md` says why, and the contract forbids the frame.
3. The saturation result kills the repair half of any docs wording. A candidate that
   tells an agent to repair, update, check or sweep documents is spending tokens on
   something two genres show it does unaided.
