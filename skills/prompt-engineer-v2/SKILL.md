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

- **Keep it short.** Prompts and skills are length-sensitive; the minimum framing is the default. Length is justified only when clarity requires it.

- **Edge-case the rule.** For any new rule, ask "where should this rule NOT fire?" Narrow the trigger or carve out exceptions explicitly. A rule that misfires on its complement creates collateral damage.

- **No overfitting to the case at hand.** When you edit a prompt motivated by a specific failure, the invariant the edit enforces defines the scope of legitimate generalization — not the case you saw fail. An edit overfits when its vocabulary, category framings, examples, or domain framing biases the agent toward passing the specific case via signal narrower than the invariant. Vectors to watch: (a) lifting words from the failing task; (b) category framings whose members map 1:1 to the case's failure modes; (c) examples that mirror the case scenario; (d) artifact-type or domain framing narrower than the invariant (e.g., "your *code* must..." when the invariant covers prose). Pre-existing baseline vocabulary is exempt from (a)–(c) but not (d) — when an edit touches narrowed framing, generalizing it is part of that edit. Examples in the prompt should collectively span domains; prefer at least one example from a domain the failing case does NOT cover.

- **Overfitting review by a fresh subagent.** Before committing a prompt edit motivated by a specific failure, hand the full edited prompt (not the diff) to a general-purpose subagent. Brief it on the invariant at stake, NOT on the failing case, its task text, or its failure mode — those are exactly the signals overfitting would leak. Ask the subagent to flag vocabulary, category framings, examples, or domain framing that overfits or narrows below the invariant's scope. If issues surface, generalize and re-review.

- **Implicit-guidance justification.** When an edit adds enforcement guidance longer than the invariant it enforces, the guidance must be justified by a prior experiment showing the agent cannot derive the guidance on its own. Experiment shape: take the prior prompt, add ONLY the invariant text as a labeled section plus a gate section asking whether the invariant holds for the output draft. Run on the failing case and read the transcript. Targeted enforcement is justified only for what the agent did NOT surface on its own; pre-specifying categories the agent would have derived itself is wasted length and an overfitting vector.

- **Recognition before enforcement.** A permanent enforcement edit is designed against what the agent can perceive about the failure, not against the failure as the editor sees it. Before locking in the fix, run a throwaway diagnostic version of the prompt — typically a one-sentence directive at the enforcement point ("after producing your draft, identify whether [invariant] holds; if not, name what is missing") — and read the transcripts. Three outcomes drive different fixes: (1) recognition succeeds and behavior changes — the diagnostic itself, possibly shortened, is the fix; (2) recognition succeeds but behavior does not — pair recognition with an action trigger (re-enter the gate, do not send); (3) recognition fails — the agent cannot perceive the failure; do not add enforcement, instead reframe the invariant in vocabulary the agent uses or add an external verifier. Permanent enforcement on top of unrecognized failure produces compliance theater. Pairs with implicit-guidance-justification: that rule answers "do not add what the agent already derives"; this one answers "do not add what the agent cannot perceive".

- **Pass percentage is not the target.** Prompt-test outcomes cluster: a structurally-fixed invariant tends to pass most fair trials; a structurally-broken one tends to fail most. That prior justifies fewer trials per conclusion, but it also makes raw pass percentage a weak target. Look for the decision point that produced the outcome. Distinguish (a) arbitrary decision points where either path should still produce valid output from (b) direct failure points where a specific action or omission made the output invalid. (a) drifts with unrelated prompt changes, model variance, and real-task distribution; if every prompt-test run takes one arbitrary path while a plausible real run may take another, add a case that exercises the other path rather than treating the percentage as stable. Example: if every run invokes a gate exactly once, that is not itself a failure, but if a plausible failure mode appears only after a second gate iteration, add or select a case that produces multiple gate iterations before claiming coverage.

- **Research conclusions must predict and be falsifiable.** "Agent behaved this way under this prompt" is one observation about one prompt, not a transferable result. A useful conclusion names a line of reasoning the agent currently uses, identifies the prompt clause that produces or permits it, and predicts what changes when you alter the clause. Form: "Currently agents may treat this line of reasoning as valid: [reasoning]. Removing or rewording [clause] suppresses this; therefore consider [edit] to tune [axis]. Predicts [behavior change]; falsified by [counter-evidence]." A finding that does not predict anything outside the case it was observed in is data, not a conclusion.

- **One falsifiable question per iteration, not one experiment.** Single-experiment iterations stop at "X did/did not happen on this run." A useful iteration runs a series of small experiments that settle one falsifiable research question about agent behavior. Plan the question first; design experiments that distinguish the candidate answers; stop when the question is answered, not at the first run.

- **Don't run the final case until you can predict the outcome.** Most iterations should not run the headline test case with the headline rubric. Borrow the case's task text for sub-experiments that probe agent behavior at smaller scope. Run the headline case only when you can confidently predict whether it will pass and why. After a failed final-case attempt, reflect on what understanding was missing rather than retrying an adjacent variant — adjacency without a diagnosis just samples a different point on the same uncharted surface.

- **Compare success and failure traces.** When a behavior the agent reliably produces in isolation (e.g., naming user types when asked directly) disappears inside a larger task, read the two reasoning traces side by side rather than assuming a capability gap. The drift is usually a recognition trigger or attention budget visible in the thinking blocks.

## Patch mode (complex edits)

For difficult prompt edits — multi-invariant rewrites, changes with non-obvious regression surface, or work the user explicitly asks to walk through — run the **patch-mode** script. It is a structured 12-step pipeline: motivation → invariant extraction → brainstorm → identify targets → draft options → context/conflict check → regression analysis → pick & full draft → deterministic check → non-deterministic check → top concerns → final.

Use it only when (a) the user asks for it, or (b) the change is complex enough that you would otherwise skip one of those steps.

Invocation:

<invoke cmd="agent-tools skill prompt_engineer_v2.do --step 1" />

The script prints the prompt for each step; follow its `NEXT STEP` instructions to advance. The principles above are already in your context, so the script does not repeat them.
