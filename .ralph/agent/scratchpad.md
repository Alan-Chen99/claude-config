# writing-for-agents loop3 — scratchpad

## Where the objective bites

The sharpest clause is *things that do not require explicit human approval to add,
but require human intervention to remove*. Every other goal (unbounded growth, doc
errors, low-supervision writing) follows from that ratchet. The question to carry
into every decision is **what retires this line**, not whether it is true.

## Durable method, reusable across rounds

**The compression rule.** Sort every line by what it is; cut in this order,
stopping at the first class that is load-bearing: (1) a **claim** — only claims
can be wrong; delete unless load-bearing and not cheaply re-derivable. (2) a
**restatement** — with two wordings nothing says which governs. (3) a **duplicate
of executable code** — replace with the script's name. (4) a **trap** — what the
reader gets wrong by default, silently. Keep. Why that order: a wrong recipe
fails loudly, a wrong claim about a recipe fails silently, and prescribing less
than the source costs efficiency rather than correctness. So deletion is the
default and each *keep* is what needs an argument.

**A null needs its second phrasing.** A single question's silence is not
evidence, because the question pre-selects what it can find. Say what a null
cannot rule out, next to the null.

**A rule stated as a removal gets checked by grepping for what was removed.**
State it as a property of the artifact with a mechanical test instead.

**A retirement condition names a comparison, not an observation.** "Retire this
if X is ever seen" retires nothing when the baseline produces X too. Write it as
"retire this when an arm carrying the line does no better than one without it" —
that is the only form a later round can act on. *(iter 6, from C2)*

## Standing `(contract)`

> An iteration may not spend its whole milestone on the prompt-test instrument
> unless that iteration also runs at least one arm against
> `sys_prompt/alan-default-next.md`. *(iter 3)*

> A prompt edit's justification lands in `sys_prompt/CLAUDE.md`, naming what would
> retire the line, in the same commit as the edit. `.ralph/agent/*` is capped and
> compressed every round, so an argument left only there is scheduled to
> disappear from under a line that stays. *(iter 4)*

> An edit that deletes or renames anything a document can point at sweeps the tree
> for citers in the same commit, and the commit says which citers were left on
> purpose. `grep -rn --include='*.md' <path-or-name> .` is the whole check.
> *(iter 5, from C3)*

> Each round either edits `sys_prompt/alan-default-next.md`, or writes into
> `sys_prompt/CLAUDE.md` what its own measurement showed that makes no edit the
> right call. The iter-3 gate above counts arms run; this one counts decisions
> reached, and a round that measures and concludes "no line is warranted here"
> satisfies it. *(iter 6, from C3)*

## Iterations 1–5 — `9f6c03a0` → `1716b706`

1–2 instrument only. 3 repriced `Omit by default` by reach and closed a cwd
leak. 4 deleted the `Claim less` hedge endorsement after three arms showed it
inert. 5 cleanup by the every-fifth-round rule: one description per case, nothing
that dates in the instrument, 13 pending banners and 3 cases deleted, references
33,360 → 15,231 tokens. Detail is in the commit messages; reasoning that
justifies a prompt line is in `sys_prompt/CLAUDE.md`.

## Iteration 6 — `1716b706` → `5e45d0b4`, plus this commit

### Critique of iterations 1–5

**C1 (workflow) — five rounds measured writing; the objective's growth clause is
about maintaining.** All thirteen cases handed the agent a blank target. Growth
is a property of repeated edits to one document, so no case that existed could
close the growth question DEC-007 opened, and rounds 4 and 5 each deferred it to
"a case that measures a document growing across sessions" without building one. A
deferral to a case that does not exist is not a plan; it is the question being
recorded instead of asked.

**C2 (fact) — DEC-008's retirement condition could not fire in the useful
direction, and two rounds treated it as the plan.** It said: retire the deletion
if an agent is found writing an unverifiable thing as a flat fact. The baseline
does that too, so the observation it named carries no information about the
clause. Iteration 4 wrote it; iteration 5 promoted it to the first item of this
round's instruction list as "the deletion's own retirement condition". Tested
this round: it fired in all three arms, the arm carrying the restored clause
included. Rewritten as a comparison in `sys_prompt/CLAUDE.md`.

**C3 (workflow) — the iter-3 contract gates on activity, and the prompt has
barely moved.** Rounds 3 and 4 both ran arms and both still spent most of their
milestone on the instrument; across five rounds `alan-default-next.md` gained one
reworded bullet and lost one clause. Running an arm is not deciding anything. New
contract above.

### The milestone

`prompt-tests/general/doc-succession`: the corpus's first case where the document
already exists. 68 committed lines; the task retracts the premise of one 22-line
section and licenses correction without naming what to correct; four other things
in the file are wrong or redundant in ways the task never mentions. Three arms —
shipped prompt, shipped + restored hedge endorsement, block deleted. Findings in
`prompt-tests/runs/doc-succession/README.md`; what they did to two open questions
is in `sys_prompt/CLAUDE.md`.

A fourth run through `task-narrow.md` — same prompt as arm A, a task that asks
only for a line to be *added* — deleted twenty lines and led its report with *I
did not add a line. A line would have made the document contradict itself.*

What the four establish, semantically: **the ratchet is not a refusal to delete,
and it is not the absence of a licence.** Every run deleted the dead section
outright, none annotated it as obsolete, all four shrank the file, and none wrote
the task's unscheduled rumour into it. The boundary they share is the **subject**:
everything about the subject the task named was rewritten, and nothing about any
other subject was touched — the unsourced release window, the rule stated twice,
the step list duplicating the script — including by the two runs that said out
loud they had found those. So documentation accumulates in regions no task ever
names, which is not a step any instruction about writing less can reach, because
writing is not where they survive.

Second finding, same runs: all three arms asserted something the repository does
not establish while deleting a section for doing exactly that. The only retraction
came from `## Before response` — one arm's own `uncertainties` list named its
inference and the hook's reply reminder came back over it. Two arms ran the same
gate and kept theirs. A prompt line about asserting what you cannot check would
be landing on ground a section written for another purpose already half holds.

**No prompt edit this round, and that is the conclusion rather than a deferral.**
The block made no difference a maintainer would care about across the three arms,
so no wording of it is supported by what was measured, and adding a line for the
scope mechanism would be adding an unproven rule — the thing the objective asks
for less of.

### `(instruction)` for iteration 7

1. **The subject boundary is the objective's live target.** Four runs agree on
   it, and no prompt line about writing less can reach past it. What has not been
   tried: a task that names one of the unnamed regions, to see whether the
   survival is scope discipline or blindness — the two have opposite fixes, and
   `doc-succession`'s fixture already carries three such regions. Do that before
   proposing any line, and hold any candidate to C2's rule: an arm carrying it
   must do better than one without.
2. Not yet through the compression rule: `.claude/skills/prompt-tests/SKILL.md`
   and `docs/prompt-testing-design.md`.

`(instruction)` Stored runs under `prompt-tests/runs/` are pinned to the prompt
commit each README names. Re-run the arm you need rather than citing them across
a prompt change.
