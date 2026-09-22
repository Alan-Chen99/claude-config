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

**Untested hypothesis.** Length hides contradictions by separation: two
conflicting sentences ~300 lines apart went unnoticed by the long version's
reader and were led with at ~80 lines apart. If true, a document's error rate
tracks the distance between related claims rather than its word count. Iteration
5 is weak evidence for it — three stale claims sat in files nobody read end to
end, and all three were found by grep, not by reading.

**A null needs its second phrasing.** A single question's silence is not
evidence, because the question pre-selects what it can find. Say what a null
cannot rule out, next to the null.

**A rule stated as a removal gets checked by grepping for what was removed.**
State it as a property of the artifact with a mechanical test instead, or the
class the argument condemns is never enumerated. See C2 below.

## Iterations 1–4 — `9f6c03a0` → `030ec831`

1–2: instrument only. `prompt-tests/CLAUDE.md` stripped of run results, two cases
deleted, the prompt-tests skill 7239 → 4405 tokens with the Iron Law removed for
contradicting the no-verdict design. 3: first measurement of the
`# Writing for other agents` block; repriced `Omit by default` by reach; closed a
cwd leak live in every run these scripts had ever made. 4: deleted the
`Claim less` hedge endorsement after three arms showed it inert, and moved the
block's reasoning into `sys_prompt/CLAUDE.md`. Detail is in the commit messages.

### Standing `(contract)`

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

## Iteration 5 — `030ec831` → `f3039915`, plus this commit

The fifth round is cleanup by the user's own rule, which is why no arm was run.
That suspends the iter-3 contract for this round only: a user instruction
overrides the between-worker contract, and the contract's grounding (two rounds
with zero measurement) is not this round's situation.

### Critique of iterations 1–4

**C1 (fact) — iteration 4 stated that no case had been through the
justify-or-remove pass. `git blame` says three had**, written in iteration 1 at
`e5f53f92`. Iteration 4 set this round's entire instruction list on that premise.
The instruction survived the error — 3 of 16 is not 0 of 16 but it is not the
pass either — and the failure is method: it read `.ralph/agent/decisions.md`,
which is the compressed copy, instead of the file the claim was about. Checking
the artifact costs one `grep`.

**C2 (workflow, the structural one) — DEC-001 applied its own argument to half
the file, and three rounds read past the other half.** Iteration 1 established
that `prompt-tests/CLAUDE.md` reaches a grader through a channel the grader
cannot decline, and removed the run results. It left the per-case entries — "is
fail", "automatic fail", "**C, M and N are scored on the returned cell alone**" —
and the three invariant statements, which say what the corpus is looking for.
Phase 1 of the dispatch withholds the reference on purpose; a description of the
probe is most of what it withholds. So the fix removed the evidence and left the
answer. Repaired in DEC-009 by stating the rule as a property with a mechanical
test rather than as a removal that was performed once.

**C3 (workflow) — the loop ships edits without sweeping citers, and has a memory
saying so since iteration 2.** Three stale claims found this round, all by grep:
`No-Amplification` cited in two live files, deleted from the prompt on
2026-09-14; `found-set-closure` telling readers `prompt-tests/CLAUDE.md` "carries
this case's arm-level results", untrue since iteration 1's own commit;
`after-the-false-page` grading against a catalogue and a 500-word figure from a
file iteration 1 decided to keep and iteration 5 deleted. Each is the objective's
"doc error in an agent-maintained codebase", and each was manufactured by an edit
in this repo. `mem-1790041345-5b39` already said to sweep, and rounds 3 and 4 did
not. A memory that is advice does not bind; the `(contract)` above does.

**C4 (workflow) — four rounds deferred one user instruction, and round 4 deferred
it while naming the deferral.** The discharge available every round was deletion,
which costs less than the review that kept postponing it. An iteration that finds
a problem in review can finish it in the same round whenever the fix is a
deletion.

### The milestone

One rule, applied everywhere it reaches: **a description of a case lives in one
place, and nothing that dates lives in the instrument.** Discharged all four
cleanup items plus the user's justify-or-remove instruction.

- 13 pending banners deleted, none renewed; 3 cases deleted whose reference was
  the whole case; 2 stamped-record stores and 1 stale note deleted.
- The 13 surviving references 33,360 → 15,231 tokens; the 3 deleted ones were a
  further 3,745. `prompt-tests/CLAUDE.md` 7,499 → 1,603.
- Every surviving case carries **Why this case is kept**.
- `after-the-false-page` is runnable again, on four defect shapes derived from
  its own fixture rather than from a deleted catalogue.

### What this does not establish

No behaviour was measured. The injection **was** reproduced in this round's own
session: one Read of a case's `task.md`, after dozens of `cat`/`sed` reads in the
same tree with no injection, attached the whole of `prompt-tests/CLAUDE.md`. What
is not established is that any grader *used* the per-case content it would have
received — unfalsifiable after the fact, and it does not gate the edit, since the
edit removes the exposure either way.

### `(instruction)` for iteration 6

1. **DEC-008's independent evaluation**, which the template requires on a later
   iteration and which is also the strongest remaining measurement: an agent
   writing for a reader about something the writer **cannot** check. That is the
   deletion's own retirement condition and the one territory
   `# Epistemic Integrity` does not reach.
2. The `Omit by default` growth question, open in `sys_prompt/CLAUDE.md`: total
   bytes went up under the shipped wording, and the objective asks that
   documentation not grow. The same fixture as (1) can carry it.
3. Not yet through the compression rule: `.claude/skills/prompt-tests/SKILL.md`
   and `docs/prompt-testing-design.md`.

`(instruction)` Stored runs under `prompt-tests/runs/` are pinned to the prompt
commit each README names. Re-run the arm you need rather than citing them across
a prompt change.
