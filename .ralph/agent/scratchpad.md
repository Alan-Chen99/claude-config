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

> Before launching the arms, the round writes down what each arm's outcome would
> mean, including the outcome that kills the candidate, and commits it. A reading
> composed after the arms are in is not admissible as the round's finding. Any
> claim that a rule delivered through a tool result caused a behaviour states the
> tool-call index of both. *(iter 7, from C3)*

## Iterations 1–6 — `9f6c03a0` → `4772ae38`

Detail is in the commit messages; reasoning that justifies a prompt line is in
`sys_prompt/CLAUDE.md`; each case's runs are under `prompt-tests/runs/<case>/`.
1–2 instrument only. 3 repriced `Omit by default` by reach and closed a cwd leak.
4 deleted the `Claim less` hedge endorsement after three arms showed it inert.
5 cleanup by the every-fifth-round rule: one description per case, 13 pending
banners and 3 cases deleted, references 33,360 → 15,231 tokens. 6 built
`doc-succession`, the first case whose subject is an edit to an existing
document, ran three arms plus a narrowed task, and shipped no prompt edit.

What survives from 6, corrected by C1 and C2 below: an agent handed a subject
rewrites everything about that subject and little about any other, the licence to
correct is not what decides it (a task asking only for an addition swept the same
way), and no arm preferred an obsolescence note to a deletion — so the growth
worry is about creation, not maintenance.

## Iteration 7 — `4772ae38` → `d978372d`, `a72fd201`, `3f2404f9`, `de85ddc9`, `c451016c`, plus this commit

### Critique of iterations 1–6

**C1 (fact)** — the "four unnamed regions" on `doc-succession` overcounts; two of
the four were correctly left alone. Corrected in `sys_prompt/CLAUDE.md`, in
DEC-010, and in the replaced memory.

**C2 (fact)** — the one retraction's mechanism was misread as `## Before response`
half-holding the ground. All four arms named the unverified claim in
`uncertainties`; detection was 4/4. What no rule covers is the transfer to the
file. Rewritten in `sys_prompt/CLAUDE.md`.

**C3 (workflow)** — five of six rounds read their arms post-hoc, so any finding
was available to be shaped by the outcome. The grader dispatch guards the grader
against that and leaves the parent, who decides, unguarded. Contract below.


### The milestone

`prompt-tests/general/uncertainty-channel`: a document whose recommended fix rests
on a premise about a vendor the repository cannot reach. Four arms — shipped
prompt, two replacements of the `Claim less` bullet, one added line in the hook's
reminder. Findings in `prompt-tests/runs/uncertainty-channel/README.md`; the
decision and what would retire it are in `sys_prompt/CLAUDE.md`.

**No edit, and the reason is not a null.** An ordering check turned the hook arm
into a second baseline sample — its prescribed sentence predates the rule by four
tool calls — and the two baseline samples then handled the same uncheckable
premise oppositely. The treated arms both landed inside that spread and neither
produced the form its own line prescribed. So the round measured its own
instrument's resolution and found it below the effect size.

### Durable method this round added

**Establish the baseline's spread before reading any difference.** A null where
arms agreed is also underdetermined: agreement was never shown to be the
baseline's normal state. This weakens iterations 4 and 6's nulls to
underdetermined rather than established, and it is the first thing to fix in the
instrument.

**A rule that arrives in a tool result explains nothing written before the first
call.** Check the tool-call index before attributing anything to a gate.

### `(instruction)` for iteration 8

1. The live target is the **transfer**: agents name an unverified claim to the
   user and leave it standing in the file, and two arms argued that reporting is
   the correct discharge of the gate. Before any wording is tried again, build the
   case that makes the baseline stable — the premise's failure needs a visible
   consequence in the fixture, and `uncertainty-channel`'s `downstream.md` is
   missing, which is the instrument for showing that base's document actually
   misleads its reader. A wording tested against an unstable baseline cannot
   separate.
2. Not yet through the compression rule: `.claude/skills/prompt-tests/SKILL.md`
   (4,431 tokens) and `docs/prompt-testing-design.md` (2,221). Iteration 10 is the
   next cleanup round by the every-fifth rule.
3. The instrument's own gap, from this round: nothing in
   `.claude/skills/prompt-tests/SKILL.md` tells a reader to check the baseline's
   spread or a rule's delivery point. Both belong there if either is to survive
   `.ralph/agent/*` compression.
