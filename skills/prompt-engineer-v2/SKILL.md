---
name: prompt-engineer-v2
description: Use whenever authoring, editing, reviewing, or reasoning about instructions, prompts, agent definitions, SKILL.md files, system prompts, CLAUDE.md files, or any other text that becomes part of an LLM's context. Provides foundational principles to keep in mind. Includes an optional "patch mode" script for difficult prompt edits — invoke patch mode only when the user requests it or when the change is complex enough to need the full structured workflow.
---

# Prompt Engineer v2

This skill is **context, not a workflow**. Read it, keep it in mind for the rest
of the task, and do not invoke a script. The script under "Patch mode" is for the
narrow case of a complex edit the user wants walked through.

## How agents fail

- **Readers differ in what they can see.** An agent inside a conversation sees
  all prior thinking and text; after compaction it sees a summary and has lost
  the detail; a subagent or a new conversation starts with none of it. Write for
  the reader who will actually have the text in front of them.
- **Agents make mistakes.** Design for "discovers its own mistakes" and "recovers
  from them", not for "always right".
- **Prompts are code.** They must work, and also be maintainable, observable, and
  propagate their errors.
- **Deterministic failure modes are the cheapest to fix.** Commands that crash or
  silently return wrong output, instructions impossible to follow because the
  state or tool is missing, "if X then Y" with no way to check X, underspecified
  specs, a pointer to a file or section that does not exist, context missing or
  arriving too late. These fail even when the agent follows instructions
  perfectly. Sweep for them before reasoning about agent
  mistakes.
- **Non-deterministic failure modes are the next layer.** Misinterpretation,
  skipping under pressure, over-application on triggers, ordering errors,
  hallucination on verification steps.

## Invariants

**Fix invariants, not symptoms.** An invariant is a structural property the
workflow guarantees probabilistically despite LLM stochasticity, **paired with
the enforcement mechanism that gives it teeth**. When a symptom appears,
identify the broken (property, enforcement) pair before patching the symptom.

- Invariant: "Workflow has no single point of failure." Enforced by: "Final
  output must pass 3 parallel runs of the reviewer step before acceptance." When
  misleading agent memory causes the reviewer to skip a check on X, the fix
  targets the *enforcement* — restore the 3-reviewer guarantee — not the X that
  was mis-reviewed. Fixing X first masks the broken invariant; the next X′ fails
  the same way.
- Invariant: "Iterative improvement converges — at termination, no candidate
  beats the chosen solution." Enforced by: "Each iteration drafts ≥2 options and
  the prior winner is always one of them." Violated when agents add options
  without revisiting the prior best; fix the option-drafting step, not the latest
  losing candidate.

**Useful invariants reject design options; artifact-existence invariants don't.**
"A block appears in the response" or "tool X is called before reply" is satisfied
by any naive option that emits the artifact, including options where the artifact
enforces nothing. Useful invariants describe *relationships between steps* —
orderings, feedback loops, asymmetric incentives, dependency chains. Sketch test:
imagine a minimal option that emits the named artifact and otherwise behaves
naively; if it satisfies your invariant while the underlying property silently
breaks, re-state the invariant as the relationship the artifact was supposed to
enforce.

**TDD for prompts.** When the broken pair is a *review pair* — its enforcement is
itself a check, test or review step — fix only the enforcement this iteration and
defer the things it reviews until a real run proves the restored review catches
them. A review "fixed" without observing it catch the failure is unverified, and
patching downstream symptoms on top of it masks both layers. Applies only to
review pairs.

## Writing the text

- **Keep it short.** Prompts and skills are length-sensitive; the minimum framing
  is the default. Length is justified only when clarity requires it.
- **Prompts have no inline comments.** Every character is consumed by the model,
  so a note to maintainers ("this section handles X", "TODO: revisit") is an
  instruction to the agent, and its intended audience will not reliably find it
  there anyway. Each prompt file needs exactly one location for maintainer-facing
  documentation — a companion CLAUDE.md, a header block with a designated marker
  — obvious to both agents and humans.
- **Rules need triggers, not just procedures.** "If git blame shows this function
  was added in the current session, it's safe to remove" looks actionable — the
  procedure for any single function is clear — but nothing tells the agent
  *which* functions to check, so the rule fires zero times. Effective rules apply
  unconditionally to a well-defined set ("every rule in this file that no step
  enumerates candidates for is dead", "all functions in this file without callers
  are dead code") or are triggered by a workflow step that enumerates the
  candidates.
- **Edge-case the rule.** For any new rule, ask "where should this rule NOT
  fire?" Narrow the trigger or carve out exceptions explicitly. A rule that
  misfires on its complement creates collateral damage.
- **Brainstorm before committing to a mechanism.** 10+ one-liner ideas spanning
  timing, actor, mechanism and scope; cluster by shared mechanism and force ideas
  into the underrepresented dimensions.
- **Two candidate mechanisms are distinct when they differ in temporal
  sequence**, not in framing. The same steps in a different order count; the same
  steps under different section labels do not. Trace each candidate as a sequence
  of moments: if the sequences do not diverge, you have one candidate written
  twice.

## Growth and removal

**Someone must do it.** If a task exists, some agent in the system must own it —
the human is not in the loop for routine work. You cannot leave a task
unassigned because it feels risky or destructive. If stale memory items need
removing, some agent removes them. Design for safe execution, not avoidance.

**Removal needs permission the agent can see.** Adding a rule, a section, a
memory entry or a function costs one edit; removing one costs a search for
whatever relies on it — so over iterations every agent adds and none removes. The
agent cannot close that gap by investigating: what is already in the file carries
no marker separating "I added this three steps ago" from "this has been here for
years", and checking the history of every line is not feasible. Each step that
can add artifacts must therefore be paired with a later step that can remove them
with equal confidence — a stated safe-to-remove rule ("a rule no step enumerates
candidates for is dead", "code not covered by tests is safe to remove"), a diff
against a named commit, or a prune step that enumerates the candidates. Without
one the workflow does not converge.

## Before you commit an edit

- **Every change is a regression risk.** A prompt change affects all invocations,
  not just the case you are optimizing for. Enumerate ≥3 scenarios where current
  behavior is correct and ask how the change could break each.
- **No overfitting to the case at hand.** When an edit is motivated by a specific
  failure, the invariant the edit enforces defines the scope of legitimate
  generalization — not the case you saw fail. An edit overfits when its
  vocabulary, category framings, examples, or domain framing bias the agent
  toward passing that case via a signal narrower than the invariant. Vectors: (a)
  lifting words from the failing task; (b) category framings whose members map
  1:1 to the case's failure modes; (c) examples mirroring the case scenario; (d)
  artifact-type or domain framing narrower than the invariant ("your *code* must
  …" when the invariant covers prose). Pre-existing baseline vocabulary is exempt
  from (a)–(c) but not (d). Examples should collectively span domains; prefer at
  least one from a domain the failing case does not cover.
- **Overfitting review by a fresh subagent.** Hand the full edited prompt, not
  the diff, to a general-purpose subagent. Brief it on the invariant at stake,
  NOT on the failing case, its task text, or its failure mode — those are exactly
  the signals overfitting would leak. Ask it to flag vocabulary, category
  framings, examples or domain framing that narrows below the invariant's scope.
  If issues surface, generalize and re-review.
- When the edit is going to be measured — cases run, transcripts read, results
  interpreted — read `experiments.md` in this skill's directory first.

## Patch mode (complex edits)

For multi-invariant rewrites, changes with non-obvious regression surface, or
work the user asks to walk through, run the **patch-mode** script: a 12-step
pipeline of motivation → invariant extraction → brainstorm → identify targets →
draft options → context/conflict check → regression analysis → pick & full draft
→ deterministic check → non-deterministic check → top concerns → final.

<invoke cmd="agent-tools skill prompt_engineer_v2.do --step 1" />

The script prints the prompt for each step; follow its `NEXT STEP` instructions
to advance.
