# writing-for-agents loop3 — scratchpad

## Where the objective bites

The sharpest clause is *things that do not require explicit human approval to add,
but require human intervention to remove*. Every other goal (unbounded growth, doc
errors, low-supervision writing) follows from that ratchet. The question to carry
into every decision is **what retires this line**, not whether it is true.

## Iteration 1 — `9f6c03a0` → `e5f53f92`

Cleaned the grader-injected file `prompt-tests/CLAUDE.md`: stripped every arm-level
count and verdict left behind by the pre-loop sweep, deleted two cases, wrote a
justification into each kept case. No prompt test ran; nothing was added to the
system prompt. Durable lessons are in memories; the rest is in git.

## Iteration 2 — `3f73a56c` → (this commit's parent)

### Critique of iteration 1

**C1 — it updated a count instead of deleting it.** In `prompt-tests/CLAUDE.md` it
removed every count as a *property of the file*. In the same commit it edited
`.claude/skills/prompt-tests/SKILL.md`'s `4 of 16 cases` to `3 of 14 cases` — the
defect it had just written a rule against, in the other half of the same
instrument, against its own memory that a count is the cheapest thing to get wrong
and the least likely to be re-derived. Deleted this round.

**C2 — it repaired one file and left the other stating the repaired file's old
contents.** SKILL.md said twice that `prompt-tests/CLAUDE.md` "carries arm-level
results". Iteration 1 is what made that false, and its commit message presents the
repair as complete. A repair that changes what a file contains is not done until
the files that describe it are swept.

**C3 — it left a hard mandate contradicting the design it was enforcing.**
SKILL.md opened with `REQUIRED SUB-SKILL: always load superpowers:writing-skills`,
RED → GREEN → REFACTOR, and the Iron Law ("no edit without a failing test first"),
while the same file forbids recording `pass`/`fail` and the user's rules say tests
are for understanding, not verdicts. Iteration 1 read and edited this file without
seeing it. The probe below shows why that is not a small miss: a reader given the
old file listed the Iron Law as checklist item 1 *and* "never stamp pass/fail"
later in the same list, flagging no conflict. The contradiction operates silently.

**C4 — a dead citation survived two sweeps.** `docs/opencode-system-prompt/baselines/`
was deleted at `42c9b9f2`; `prompt-tests/CLAUDE.md` still pointed inside it.

### Why compress the skill, rather than probe the system prompt

Two iterations have now touched only the instrument, which needs a reason beyond
convenience. It is this: the skill is the only file in the stack that prescribes a
*method*, and the method it prescribed was the one the redesign rejected. Any probe
run before the repair is run under a contradicted method by an agent that reads it.
And the objective names this file by name as the compression case, so doing it is
the experiment, not a detour from it.

### The compression rule (the reusable output)

Sort every line by what it is; cut in this order, stopping at the first class that
is load-bearing:

1. **a claim** — a fact about the world. Only claims can be wrong. Delete unless
   load-bearing *and* the reader cannot cheaply re-derive it.
2. **a restatement** — a second wording of something this file, or a file it points
   at, already says. Delete: with two wordings, nothing says which governs.
3. **a duplicate of executable code** — prose describing what a script already
   enforces and reports. Replace with the script's name.
4. **a trap** — what the reader gets wrong by default, where being wrong is silent.
   Keep. This is what the document is for.

Why that order: a wrong recipe fails loudly, a wrong claim about a recipe fails
silently. And prescribing less than the source costs efficiency, not correctness —
the floor is a reader with no document rediscovering the same things, slower. Which
is why the cut is safe by default and each *keep* is what needs an argument.

Applied: 7,239 → 4,390 tokens, 531 → 331 lines, no `# Pitfalls`-class content lost.

### What the probe showed

Two readers, one per version, same question ("list every precondition you must get
right, what goes wrong if you miss it, and whether you would notice"), no repo
access, staged outside `prompt-tests/`.

- **Nothing load-bearing was lost but one thing**, which the probe caught: the
  reasoning-capture trap (`--thinking-display summarized`; without it every thinking
  block is an empty string while the token count still reports, so the log looks
  like an agent that did not reason). Restored as a clause.
- **The compression surfaced a contradiction the long version hid**: "one grader per
  arm" against "give the grader both sessions labelled A and B". Both sentences were
  in the old file, ~300 lines apart, and its reader did not see it; at ~80 lines
  apart the new file's reader led with it. Repaired by making the blind A/B pass a
  separate dispatch.

  Hypothesis for why, worth testing rather than believing: **length hides
  contradictions by separation**, so compression is a correctness instrument and not
  only a cost reduction. If that holds it is the mechanism behind the goal of fewer
  doc errors over time — and it predicts that a document's error rate should track
  the *distance between related claims*, not its word count. Untested.

### Held with low confidence

The `pre_output.record` confound paragraph I added to the skill is the one addition
this iteration made. Neither probe reader picked it up as actionable. It is
re-derivable from the prompt itself so it cannot rot, but if iteration 3 or 4 finds
no use for it, delete it rather than leaving it to be inherited.

### Open

- The `# Writing for other agents` block is still unmeasured. Nothing this loop has
  done yet bears on whether its "better off with a hint" bullet pushes the wrong way
  (`notes/workers-bullet-hint-in-fact-position.md` argues the hint form has the worst
  retirement profile of the placements it compares). That is a probe, not a read.
- `after-the-false-page` is still not runnable; it is the only case that measures a
  document *growing*.
- `payments-relay/` is 12.9k words held alive by three citations.
- `prompt-tests/CLAUDE.md` is 7,496 tokens and reaches every grader. The same
  compression rule applies to it and has not been run.
