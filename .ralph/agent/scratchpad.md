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
> repo — or records that it looked and found none. *(22; see C2)*

> **The round ends under the user's `.ralph/agent/*` ceiling, with the number in
> its last commit message.**
> `cat .ralph/agent/* | agent-tools count-tokens --file /dev/stdin` < 6000.

> Operational rules for running, grading and deleting prompt tests live in
> `.claude/skills/prompt-tests/SKILL.md` and are not restated here.

## History — rounds 1–21, `9f6c03a0` → `0a2ade7e`

Anything justifying a prompt line lives in `sys_prompt/CLAUDE.md` — the durable
home, and the file to read before touching the block. Everything else is in the
commit messages. Shipped: `Say what ends it` (9). Deleted: `Omit by default`
(13, 17), `Claim less` (4, 14). Eight candidate wordings failed (3–8, 12, 14, 16,
18, 20, 21), the last four all claim-handling. Round 10 fixed a nine-round
harness contamination and voided every arm stored before 2026-09-22. Every
sentence still in the block has been measured alone.

## Iteration 22 — `942cf683` → `06679ac6` (context)

Diagnosed a live session rather than a fixture, and falsified the block's
standing explanation of documentation growth: growth has a moment, and a
document soliciting additions supplies it. Ran the `busiest-few` probe four
ways (`6b52d254` … `fa5128ea`; restore with `git checkout 307ccfa6 --
prompt-tests/runs/busiest-few`). Candidate 1, aimed at inherited defects,
bought nothing — those go to the reply, which the response template already
slots. Candidates 2 and 3 are one claim under two vocabularies; each met its
pre-registered ship criterion and neither shipped, because 22 read two
collateral costs as outranking it.

## Iteration 23 — `06679ac6` → `d8a0aeef` + this commit

### Critique of 22

**C1 (fact — the cost that stopped the ship is the fixture's own house style,
checkable with no run).** 22 blocked the ship on: the treated arms omit
argparse's `metavar`, so their `docs/report.md` says `[--top N]` while `--help`
prints `[--top TOP]`. The fixture's only other option is
`rep.add_argument("--since")` — no `metavar`, no `help` — and its
`docs/report.md` documents it as `--since YYYY-MM-DD`. **The delivered
documentation contradicted the delivered program before any arm ran.** The arms
that omitted `metavar` matched the one neighbour they had; the arms that set it
improved on house style. 22 priced this as "a correctness defect in the one file
the line steers content toward". Its accompanying claim — *no arm on either side
reasons about that surface* — is also false: the candidate-1 arm's thinking says
"I'll wire this into the argument parser with metavar N".

**C2 (fact — the second cost has an alternative reading 22 never excluded).**
22 recorded that both treated arms "dropped the `--since` interaction" and
called that under-documentation. Displacement fits the same observation: the
untreated arm filed the tie-break fact in `CONVENTIONS.md` and the composition
sentence in `docs/report.md`; the treated arms filed the tie-break in
`docs/report.md` and left the composition out, at about equal bullet length. If
that is what happened the line wrote no less — it routed a self-made fact into
the slot another fact held. The pre-registration could not separate the two, so
the cost is underdetermined rather than established, and it decided the round.

**C3 (workflow — an unexplained observation became a standing blocker in the
durable home).** `sys_prompt/CLAUDE.md` now reads "…the split is observed and
unexplained, which is why none is shipped". The user's rule is that a claim is
valid only with a hypothesis of why beside it; this one states it has none, and
it is the reason a measured effect does not ship. A sentence that blocks an
action and names no observation that would lift it is the ratchet the objective
targets: nothing a later round can see retires it.

**C4 (workflow — 22's instruction 1 prescribes what the user's guidance rules
out).** *Default to `n=1`. If you want more, build new cross-domain test cases;
do not replicate.* Instruction 1 is a re-run of one arm of the same fixture, and
a third draw on a 2-vs-2 split settles nothing either way. **Override of
instruction 1.** Instruction 3 — build the second genre rather than re-running
this one — is taken instead, and C1 removes the question instruction 1 existed
to answer.

### Why this milestone

After C1 and C2 the only live doubt about candidate 3 is the one DEC-030 named
as its framing bias: the claim was found and measured on a single fixture, whose
soliciting document is a `## Gotchas` list with an explicit invitation. The live
session that motivated the claim solicits differently — an `Agent Policy` under
a `CLAUDE.md`, auto-loaded, with no invitation at all. A second genre answers
whether the effect is the claim's or that fixture's, which is what ship-or-delete
turns on; another draw on `busiest-few` answers nothing.

### The round's work and result

Probe `hushed-rollcall`, two arms, pre-registration `08d4bcef`. **Outcome A.**
The treated arm left `## Agent Policy` untouched and put the fact in
`docs/cli.md` and in a comment beside the line it governs; the untreated arm
added a standing rule about its own implementation's output buffer. Both arms
sent the inherited defect to the reply, unaided, as the hypothesis predicts.
Attribution, non-blind, the treated arm's own reasoning: *the new detail … is
just a consequence of my specific change rather than a general project property,
it belongs in `docs/cli.md` instead* — the line's vocabulary, none of which
occurs anywhere in the fixture. The decisive reading was blind, and it preferred
the arm that grew, on the strength of the standing rule that arm added.

The pre-registered discriminator for C2 came back against suppression: nothing
`base` states about behaviour that existed before the session is missing from
`cand`'s `docs/cli.md`.

Shipped, byte-identical to the measured arm; 6395 → 6464 API tokens. The probe
is promoted to `prompt-tests/general/hushed-rollcall`, because the paragraph it
now owns had no case at all and its retirement condition could not be observed
by anyone. `busiest-few` deleted.

### `(instruction)` for iteration 24

1. The help-surface cost is two-for-two across genres and has a hypothesis and
   no test. Test the hypothesis, not the wording: give an arm carrying the line
   a task with **no** documentation ask in it. If it still does less than an
   untreated arm beyond the literal request, the cost is an attention effect and
   no rewording reaches it.
2. Do not reword the shipped bullet from this round's observations. It was
   composed before the arms and has now been measured twice; a wording composed
   after the arms is the overfitting the repo's own hints name.
3. Neither arm priced an end for anything it wrote, in any position, though both
   carried `Say what ends it`. Two bullets now pull on the same act. The
   compression rule's first question for the next round is whether one of them
   is a restatement of the other.

