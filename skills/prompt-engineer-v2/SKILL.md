---
name: prompt-engineer-v2
description: Use whenever authoring, editing, reviewing, or reasoning about instructions, prompts, agent definitions, SKILL.md files, system prompts, CLAUDE.md files, or any other text that becomes part of an LLM's context. Provides foundational principles to keep in mind. Includes an optional "patch mode" script for difficult prompt edits — invoke patch mode only when the user requests it or when the change is complex enough to need the full structured workflow.
---

# Prompt Engineer v2

This skill is **context, not a workflow**. When it activates, read the principles below and keep them in mind for the rest of the task — do not invoke a script. The script under "Patch mode" exists for the narrow case of a complex edit the user explicitly wants walked through.

## Principles to keep in mind

Apply these whenever you are writing, editing, or critiquing any text that becomes part of an LLM's context (prompts, instructions, skills, agent definitions, CLAUDE.md, hooks, etc.).

1. **Know your observability.** Claude Code conversations produce JSONL logs containing both thinking and text blocks. An agent within a conversation sees all prior thinking and text. Context compaction replaces full history with a summary — the agent loses detail. A new agent (subagent, next conversation) starts with zero prior context. Use `/cc-history` to query conversation logs when you need evidence of what actually happened.

2. **Agents make mistakes.** Do not design for "always right." Design for "discover own mistakes" and "recover from mistakes." Verification and self-correction matter more than perfection.

3. **Prompts are code.** They must work, but also be maintainable, observable, and propagate errors. Apply the same engineering standards you would to source code: clarity, testability, failure transparency.

4. **Fix invariants, not symptoms.** An invariant is a structural property the workflow guarantees probabilistically despite LLM stochasticity, **paired with the enforcement mechanism that gives it teeth**. Examples illustrate the pair shape — they are not a checklist:

   - Invariant: "Workflow has no single point of failure."
     Enforced by: "Final output must pass 3 parallel runs of the reviewer step at the same time before acceptance."
     When violated (e.g., misleading agent memory causes the reviewer to skip a check on X): the fix targets the *enforcement mechanism* — restore the 3-parallel-reviewer guarantee — not the X that was mis-reviewed. Fixing X first masks the broken invariant; the next X′ fails the same way.

   - Invariant: "Iterative improvement converges — at termination, no candidate beats the chosen solution."
     Enforced by: "Each iteration drafts ≥2 options and the prior winner is always one of them."
     When violated: agents add new options without revisiting the prior best, divergence — fix the option-drafting step, not the latest losing candidate.

   Rule: when a symptom appears, identify the broken (property, enforcement) pair before patching the symptom.

5. **TDD for prompts.** When the broken pair is a *review pair* (its enforcement mechanism is itself a check/test/review step), only fix the enforcement mechanism in this iteration. Defer fixing the things-it-reviews until a real run proves the restored review now catches them. A review "fixed" without observing it catch the failure on a real run is unverified; patching downstream symptoms on top of an unverified review masks both layers of bug. This is the prompt analogue of test-driven development: prove the test fails on the bug before fixing the code. Apply this rule ONLY when the broken pair is a review pair.

6. **Someone must do it.** If a task exists, some agent in the system must own it — the human should not be in the loop for routine work. When designing workflows, every necessary action must be assigned to an agent. You cannot leave a task undone because it feels "risky" or "destructive." If an agent memory system needs stale items removed, some agent removes them. Design for safe execution, not avoidance.

7. **Permission to undo.** Every iteration's output must be safely reversible by the next agent. If agent N adds a function, agent N+1 must have the means to determine whether removing it is safe (e.g. "diff with [commit] first"). When the workflow does not provide that means, agents accumulate dead code, stale rules, and cargo-culted artifacts they are afraid to touch. Prompts must ensure each agent has the information needed to confidently undo, replace, or remove what prior agents produced.

8. **Agents won't search for permission to remove.** From the agent's perspective, all existing functions look the same — there is no visible marker distinguishing "I added this 3 steps ago" from "this has existed for years." Checking `git blame` on every function is not feasible: there are too many. If the agent cannot immediately see that removal is safe, it leaves the code in place.

9. **Rules need triggers, not just procedures.** A rule like "if git blame shows this function was added in the current session, it's safe to remove" looks actionable — the procedure for any single function is clear. But the rule is inert because nothing tells the agent *which* functions to check. There are hundreds of functions; the agent has no reason to run `git blame` on any particular one. The procedure is followable, the trigger is missing, so the rule fires zero times. Effective rules either apply unconditionally to a well-defined set (e.g., "all functions in this file without callers are dead code") or are triggered by a workflow step that enumerates the candidates.

10. **Adding is cheap, removing is expensive.** Writing a function, argument, or if-statement costs one edit. Removing one requires searching files, checking callers, verifying no external consumers, confirming nothing in memory depends on it. Over iterations this asymmetry causes unbounded growth — each agent adds, none remove. Counteract it with safe-to-remove rules (e.g., "all code not covered by tests is safe to remove", "functions without callers in this module are dead code") and explicit review-and-prune steps. If a workflow step can add artifacts, a later step must be able to remove them with equal confidence — otherwise the workflow will not converge.

11. **Prompts have no inline comments.** Source code has syntax for comments (`//`, `#`, `/* */`) that compilers and interpreters skip. Prompts have no such syntax — every character is consumed by the model. Text intended as a note to maintainers ("this section handles X", "TODO: revisit") becomes an instruction to the agent. Each prompt file must have exactly one unambiguous location for maintainer-facing documentation (e.g., a companion CLAUDE.md, a header block with a designated marker, or a separate doc file). This location must be obvious to both agents and humans reading the file. Never scatter explanatory notes, TODOs, or rationale inline within prompt text — they will be interpreted as instructions, and their intended audience (the maintainer) will not reliably find them there anyway.

## Additional suggestions to keep in mind

- **Useful invariants reject design options; artifact-existence invariants don't.** "A block appears in the response" or "tool X is called before reply" is satisfied by any naive option that emits the artifact, including options where the artifact no longer enforces anything. Useful invariants describe *relationships between steps* — orderings, feedback loops, asymmetric incentives, dependency chains. Sketch test: imagine a minimal naive option that emits the named artifact but otherwise behaves naively. If the sketch satisfies your invariant while the underlying property silently breaks, re-state the invariant as the relationship the artifact was supposed to enforce.

- **Distinct workflow options differ in temporal sequence**, not in framing. Same steps in a different order count; same steps with different prompt-section labels do not. A reader tracing the reasoning log should see different intermediate states at different points in time.

- **Every change is a regression risk.** A prompt change affects all invocations, not just the case you are optimizing for. Before committing wording, enumerate ≥3 scenarios where current behavior is correct and ask how the change could break each.

- **Deterministic failure modes are the cheapest to fix.** Commands that may crash or silently return wrong output, instructions impossible to follow because state/tools are missing, "if X then Y" with no way to check X, underspecified specs, and missing context (or context provided too late) all fail even when the agent follows instructions perfectly. Sweep for these before reasoning about agent mistakes.

- **Non-deterministic failure modes are the next layer.** Misinterpretation (multiple readings), skipping under pressure, over-application (false positives on triggers), ordering errors, and hallucination on verification steps. Severity ≥ medium warrants a revision.

- **Brainstorm before committing to a mechanism.** Quantity over quality: 10+ one-liner ideas spanning timing (before/during/after/periodic), actor (agent/system/user/tool/separate process), mechanism (rule/example/tool/workflow step/system injection), and scope (per-item/per-task/per-session/global). Cluster by shared mechanism; if >3 ideas share one, force ideas into underrepresented dimensions.

## Patch mode (complex edits)

For difficult prompt edits — multi-invariant rewrites, changes with non-obvious regression surface, or work the user explicitly asks to walk through — run the **patch-mode** script. It is a structured 12-step pipeline: motivation → invariant extraction → brainstorm → identify targets → draft options → context/conflict check → regression analysis → pick & full draft → deterministic check → non-deterministic check → top concerns → final.

Use it only when (a) the user asks for it, or (b) the change is complex enough that you would otherwise skip one of those steps.

Invocation:

<invoke cmd="agent-tools skill prompt_engineer_v2.do --step 1" />

The script prints the prompt for each step; follow its `NEXT STEP` instructions to advance. The principles above are already in your context, so the script does not repeat them.
