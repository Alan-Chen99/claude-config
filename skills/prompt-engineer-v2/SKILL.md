---
name: prompt-engineer-v2
description: Use whenever authoring, editing, reviewing, or reasoning about instructions, prompts, agent definitions, SKILL.md files, system prompts, CLAUDE.md files, or any other text that becomes part of an LLM's context. Provides foundational principles to keep in mind. Includes an optional "patch mode" script for difficult prompt edits — invoke patch mode only when the user requests it or when the change is complex enough to need the full structured workflow.
---

# Prompt Engineer v2

This skill is **context, not a workflow**: keep it in mind for the whole task.

## Principles

- **Readers differ in what they can see.** After compaction an agent has a
  summary, a subagent or new session nothing: write for the reader who will
  have the text in front of it.
- **Prompts are code, run by an agent that errs.** They must work, stay
  maintainable and observable, propagate errors, and let it discover and recover
  from mistakes.
- **Every character is an instruction.** Keep framing minimal. Maintainer
  notes read to the agent as instructions; keep them in one place all
  maintainers find, such as a companion CLAUDE.md.
- **Fix invariants, not symptoms.** Rule out deterministic failures, then find
  the broken pair: a structural property and the enforcement giving it teeth,
  like "no single point of failure" enforced by "output passes 3 parallel
  reviewer runs". If a reviewer skipped a check on X, restore the 3-run
  guarantee, not X: fixing X masks the broken pair, so X′ fails next. Test each
  property: if a naive design that merely emits the named artifact (a block, a
  tool call) satisfies it, restate it as a relationship between steps
  (ordering, feedback loop, dependency).
- **TDD for prompts.** When the broken enforcement is itself a check, test or
  review, fix only it; defer what it reviews until a real run shows it catching
  the failure: patched symptoms would hide whether it works.
- **Removal needs permission the agent can see.** Adding costs an edit, removing
  a search for dependents, and no line shows if it is three steps or three years
  old, so agents only add. Pair each step that can add artifacts with one that
  removes them as confidently: a stated safe-to-remove rule, a diff against a
  named commit, or a prune step enumerating candidates. **Someone must do it**:
  a workflow gives every routine task, destructive ones included, to an agent
  with a safe procedure, not to the human.

## Checklist for each edit

- **Deterministic failures first**: they occur even under perfect obedience.
  Commands crashing or exiting 0 with wrong output, steps needing absent state
  or tools, "if X" with X uncheckable, underspecified specs, dangling pointers,
  context missing or late. Then misreading, skipping under pressure,
  over-applied triggers, misordering, hallucinated verification.
- **Rules need triggers, not just procedures.** "If git blame shows a function
  is new, it may go" fires zero times: nothing says which functions to check.
  Cover a defined set unconditionally, or have a step enumerate the candidates.
  Then **edge-case the rule**: where should it NOT fire?
- **Regressions**: name ≥3 scenarios where current behavior is correct and how
  the change could break each.
- **No overfitting to the case at hand.** When a failure motivates the edit, the
  invariant, not the case, sets its scope: no words lifted from the case,
  categories mapping 1:1 onto its failures or examples mirroring it, unless the
  prompt already had them; no artifact-type or domain framing narrower than the
  invariant ("your *code* must…" when it covers prose). Examples span domains,
  at least one the case does not touch.
- **Overfitting review by a fresh subagent**: give it the full edited prompt and
  the invariant, never the failing case, its text or failure mode, and ask what
  narrows below the invariant; generalize any finding and re-review.
- Running cases or reading transcripts? First read this skill's
  `experiments.md`.

## Patch mode

Only for multi-invariant rewrites, a non-obvious regression surface, or on user
request: run the script and follow each `NEXT STEP`.

<invoke cmd="agent-tools skill prompt_engineer_v2.do --step 1" />
