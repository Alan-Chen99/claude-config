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
tracks the distance between related claims rather than its word count.

**A null needs its second phrasing.** DEC-005's instrument is sound and its
positive findings stand; a single question's silence is not evidence, because the
question pre-selects what it can find. Say what a null cannot rule out, next to
the null.

## Iterations 1–3 — `9f6c03a0` → `59511d7c`

1–2 touched only the instrument: `prompt-tests/CLAUDE.md` stripped of run
results, two cases deleted, `.claude/skills/prompt-tests/SKILL.md` 7239 → 4405
tokens with the Iron Law removed for contradicting the no-verdict design.
3 measured the `# Writing for other agents` block for the first time, repriced
`Omit by default` by reach, and closed a cwd leak (case slug in the tested
agent's cwd) live in every run these scripts had ever made. Detail is in the
commit messages and in `prompt-tests/runs/what-retires-this-line/README.md`.

### `(contract)` from iteration 3

> An iteration may not spend its whole milestone on the prompt-test instrument
> unless that iteration also runs at least one arm against
> `sys_prompt/alan-default-next.md`. Instrument repairs ride along with
> measurement of the target; they do not substitute for it.

Grounded: two consecutive iterations had produced zero measurements of the file
the objective names.

## Iteration 4 — `59511d7c` → `8b122ac7`, plus this bookkeeping commit

### Critique of iteration 3

**C1 (fact/workflow) — DEC-007 was decided on the one metric the objective does
not name, and the metric it does name ran the other way.** The objective asks
that documentation not grow unbounded. On the motivating case the pre-edit arm
wrote 2561 bytes in total; the shipped arm wrote 793 + 3212 = 4005. Iteration 3
put that in a parenthetical and chose per-session read cost as the quantity that
matters, without arguing it against the objective's own criterion — and the
user's framing in this same objective says *relocation is growth*. I checked
whether the edit survives on a different ground and it does: the shipped arm's
`CLAUDE.md` addition names the trap (the vendor's documented 1000-record limit is
not the binding constraint) and points at the detail, where the pre-edit arm
inlined all of it. So the decision stands on a **semantic** reading that was
never written down, and its recorded basis is a number the objective never asked
for. Both halves now sit in `sys_prompt/CLAUDE.md`, growth question included, as
unresolved rather than parenthetical.

**C2 (workflow, the structural one) — the justification for a shipped prompt line
went into loop-local state.** `sys_prompt/CLAUDE.md` is where this repo's own
doctrine puts the reasoning, dates and measurements behind a prompt line; that
file carried nothing at all about `# Writing for other agents`. Iteration 3's
edit shipped with its argument only in `.ralph/agent/decisions.md` and a run
README — and `.ralph/agent/*` is capped at 6000 tokens and compressed every
round, so the line was set to outlive the argument for it. A line nobody can
evaluate is a line nobody can remove: the loop was manufacturing the exact thing
the objective is against. See the `(contract)` below.

**C3 (user instruction unexecuted, three rounds running) — "remove or replace
other test cases on the Writing block; each one kept you must justify that the
test case is providing positive value."** Iteration 1 deleted two cases on a
different argument (DEC-002's ratchet reasoning) and no case has been through the
justify-or-remove pass. Meanwhile 13 `reference-solution.md` files still carry
*Not to be used until checked against the current grading design*, added
pre-loop; nothing has checked one, and iteration 1's own memory records that
bannering is the ratchet the objective is against. Handed to the cleanup round
below, concretely enough that it cannot be deferred a fourth time.

**C4 — iteration 3 shipped a prompt edit with no grader**, where
`.claude/skills/prompt-tests/SKILL.md` requires a blind comparison for a prompt
edit specifically. It recorded the gap instead of closing it or amending the
skill. Closed this round by running one.

### `(contract)` amendment — added by iteration 4, from C2

> A prompt edit's justification lands in `sys_prompt/CLAUDE.md`, naming what
> would retire the line, in the same commit as the edit. `.ralph/agent/*` is
> capped and compressed every round, so an argument left only there is scheduled
> to disappear from under a line that stays.

### The milestone: the `Claim less` hedge clause

Chosen because it is the one clause in the prompt that *manufactures* the thing
the objective's hardest bullet is against, and because the objective names the
note that analyses it while nothing had measured it.

New case `unconfirmed-cause` (thumbd, a different domain from the sync.sh
fixture): a handover carrying an unexplained workaround that works, a belief of
the reporter's that is **false and checkable in one read**, an unverifiable
second-hand rumour, and a non-reproduction. The false-and-checkable item is the
discriminator — repeating it as a warning is hedging where checking was
available. The unexplained workaround is the control in the other direction: it
is load-bearing and nothing will ever retire it, so an arm that drops everything
unretirable fails there.

Three arms, one sentence apart. **Result: the clause is inert here.** With it and
without it the agent reached the same four verdicts, measured the lock against a
live `LOCK_EX` writer rather than reading the source, computed the same
`(39/40)^30`, and changed no behaviour. The blind grader found "the same work"
and, on hedging where checking was available, "neither". Arm D, which *priced*
the hedge rather than deleting it, wrote 30% more and rewrote `source_bytes`
mid-investigation where both others declined in writing.

**Why inert rather than merely unmeasured.** `# Epistemic Integrity`'s No
Unexplained Residue Rule forbids what the clause would license, and
unconditionally where the clause said *often*. So the clause is inert where that
section reaches and harmful where it does not — deletion is right under either
reading, which is what makes this more than a null. Shipped as deletion.

### What this does not establish

n=1 per arm, one fixture, one model. Every item was checkable from the fixture or
by arithmetic, and the agent was writing up **its own** investigation, which is
exactly No Unexplained Residue's territory — so the two sections overlap by
construction here. The over-claims and stale line refs the grader found in the
clause-carrying arm are single instances and are **not** attributed to the
sentence. The untested case: an agent writing for a reader about something the
writer cannot check.

### `(instruction)` for iteration 5 — the cleanup round

Fifth round is cleanup. These are the items, and each has been deferred at least
once:

1. Delete `prompt-tests/payments-relay/` with its citers. DEC-003's two-round
   clause is **spent** as of this iteration; it has said what it was going to say
   and is not evidence for keeping anything a third time.
2. The justify-or-remove pass on the cases bearing on `# Writing for other
   agents`, per the user's instruction. The 13 *Not to be used until checked*
   banners are the same sweep: check, repair, or delete the case — do not
   re-banner.
3. `docs/opencode-system-prompt/trials/`, 22.8k tokens of pass/fail-stamped
   records under a design that rejects pass/fail, several for cases iteration 1
   deleted. `prompt-tests/CLAUDE.md:113` says "Leave them as they are", which is
   the permanence this objective is against. Sweeping the citers in
   `notes/compliance-check-failure-mode/` is part of the work.
4. `prompt-tests/CLAUDE.md` at ~7.5k tokens has never been through the
   compression rule.

Not cleanup, and the strongest remaining measurement: a case where the writer
**cannot** check what it is writing about, which is the only territory where the
deleted clause could still have been doing work — and the same fixture would test
the `Omit by default` growth question in C1.

`(instruction)` The stored runs under `prompt-tests/runs/` were taken against
particular prompt commits named in each README. Re-run the arm you need rather
than citing them across a prompt change.
