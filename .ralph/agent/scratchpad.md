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

> Operational rules for running, grading and deleting prompt tests live in
> `.claude/skills/prompt-tests/SKILL.md` and are not restated here.

## History — rounds 1–24, `9f6c03a0` → `b7e01d08`

Anything justifying a prompt line lives in `sys_prompt/CLAUDE.md` — the durable
home, and the file to read before touching the block. Everything else is in the
commit messages. Shipped: `Say what ends it`, and the self-consequence bullet.
Deleted: `Omit by default`, `Claim less`, and the help-surface cost paragraph.
Eight candidate wordings failed, the last four all claim-handling. Round 10 fixed
a nine-round harness contamination and voided every arm stored before 2026-09-22.
Every sentence still in the block has been measured alone. 22 diagnosed a live
session rather than a fixture; 23 shipped the bullet across two genres; 24 ran a
third, deleted the cost paragraph it had written after its own arms, and wrote a
new one the same way — see C1.

## Iteration 25 — `b7e01d08` → ...

### Critique of 24

**C1 (fact — the round's headline hypothesis names a fixture property that has
never existed in any fixture).** 24 withdrew *only a self-made fact has no slot*
and installed, in `sys_prompt/CLAUDE.md` and in a memory, *the heading takes
whatever the tree houses nowhere … the lever is a required home rather than an
instruction to write less*, on the stated ground that `weary-waitlist` "gave the
self-made fact a required home the earlier fixtures did not give it". All three
fixtures give it one, in one line of their own auto-loaded `CLAUDE.md`:
`hushed-rollcall`, *Every subcommand and option of `bin/warden` is described in
`docs/cli.md`*; `busiest-few` (`git show c28e1ac5:…/fixture/CONVENTIONS.md`),
*Every user-visible flag is described in `docs/report.md`*; `weary-waitlist`,
*Every flag of `bin/spool` has a row in `README.md`'s flag table*. The round
rewrote `hushed-rollcall/reference-solution.md` in the same iteration and its own
repair names `docs/cli.md` as "which the same `CLAUDE.md` names as where every
option is described". So the comparison was uncontrolled, not reversed, and the
hypothesis, its retirement condition, and instructions 2 and 3 all rest on a
difference that is not in the tree. Withdrawn here, not replaced: the three
fixtures also differ in whether the task asks for documentation at all and in
what their soliciting heading solicits (*learn* vs *find*), and no round
controlled either.

**C2 (workflow — the loop reproduces the growth the objective is against, in its
own state).** `.ralph/agent/*` went 5071 → 5988 tokens in one round, and the
round's answer to breaching the 6000 ceiling was to shorten the ceiling clause
(`40e384d4`), not to cut content. Round narrative is the growth: 24's own section
was ~1400 tokens of material the contract already routes to commit messages and
to `sys_prompt/CLAUDE.md`. Compressed here to the paragraph above.

**C3 (workflow — the guard against composed-after-the-arms readings covers
wordings only).** The contract requires an occurrence outside the round's own
fixtures *before a candidate wording is written*, and requires pre-registration
*before launching the arms*. A claim about how fixtures differ is neither, so C1
walked straight through both. One grep of three files would have killed it.
Amended below.
