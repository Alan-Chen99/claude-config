<!-- step 1: motivation -->

# First Principles

Keep in mind throughout this workflow:

1. **Agents make mistakes.** Do not design for "always right." Design for "discover own mistakes" and "recover from mistakes." Verification and self-correction matter more than perfection.

2. **Prompts are code.** They must work, but also be maintainable, observable, and propagate errors. Apply the same engineering standards you would to source code: clarity, testability, failure transparency.

3. **Think forward from the prompt.** Prompts provide logical invariants — the agent "should" behave correctly given these instructions. When it doesn't, there is a hole in the logic. Find the hole. If your function crashes on input `9`, you don't add `if input == 9: return special_case` — you ask "this code is supposed to handle all inputs, why didn't it?" and fix the actual bug. Same with prompts: don't patch the symptom, fix the invariant that failed.

4. **Someone must do it.** If a task exists, some agent in the system must own it — the human should not be in the loop for routine work. When designing workflows, every necessary action must be assigned to an agent. You cannot leave a task undone because it feels "risky" or "destructive." If an agent memory system needs stale items removed, some agent removes them. Design for safe execution, not avoidance.

5. **Permission to undo.** Every iteration's output must be safely reversible by the next agent. If agent N adds a function, agent N+1 must have the means to determine whether removing it is safe (e.g. "diff with [commit] first"). When the workflow does not provide that means, agents accumulate dead code, stale rules, and cargo-culted artifacts they are afraid to touch. Prompts must ensure each agent has the information needed to confidently undo, replace, or remove what prior agents produced.

6. **Agents won't search for permission to remove.** From the agent's perspective, all existing functions look the same — there is no visible marker distinguishing "I added this 3 steps ago" from "this has existed for years." Checking `git blame` on every function is not feasible: there are too many. If the agent cannot immediately see that removal is safe, it leaves the code in place.

7. **Rules need triggers, not just procedures.** A rule like "if git blame shows this function was added in the current session, it's safe to remove" looks actionable — the procedure for any single function is clear. But the rule is inert because nothing tells the agent *which* functions to check. There are hundreds of functions; the agent has no reason to run `git blame` on any particular one. The procedure is followable, the trigger is missing, so the rule fires zero times. Effective rules either apply unconditionally to a well-defined set (e.g., "all functions in this file without callers are dead code") or are triggered by a workflow step that enumerates the candidates.

8. **Adding is cheap, removing is expensive.** Writing a function, argument, or if-statement costs one edit. Removing one requires searching files, checking callers, verifying no external consumers, confirming nothing in memory depends on it. Over iterations this asymmetry causes unbounded growth — each agent adds, none remove. Counteract it with safe-to-remove rules (e.g., "all code not covered by tests is safe to remove", "functions without callers in this module are dead code") and explicit review-and-prune steps. If a workflow step can add artifacts, a later step must be able to remove them with equal confidence — otherwise the workflow will not converge.

9. **Prompts have no inline comments.** Source code has syntax for comments (`//`, `#`, `/* */`) that compilers and interpreters skip. Prompts have no such syntax — every character is consumed by the model. Text intended as a note to maintainers ("this section handles X", "TODO: revisit") becomes an instruction to the agent. Each prompt file must have exactly one unambiguous location for maintainer-facing documentation (e.g., a companion CLAUDE.md, a header block with a designated marker, or a separate doc file). This location must be obvious to both agents and humans reading the file. Never scatter explanatory notes, TODOs, or rationale inline within prompt text — they will be interpreted as instructions, and their intended audience (the maintainer) will not reliably find them there anyway.

# Prompt Patch - Motivation

Why make this change? What goes wrong if we do nothing?

Write out:

1. **The problem**: What specific behavior needs to change? Be concrete (quote output, describe failure mode, show example).
2. **Cost of inaction**: What happens if no prompt change is made? Who is affected and how?
3. **Success criteria**: How will you know the change worked? What observable difference?

NEXT STEP:
<invoke working-dir="~/.claude/skills/scripts" cmd="python3 -m skills.prompt_patch.do --step 2 --problem='...' --cost='...' --success-criteria='...'" />
Execute this command now.

<!-- step 2: brainstorm -->

# Prompt Patch - Brainstorm

Before designing workflow options, generate a rapid, unfiltered list of ideas.

**Instructions:**
1. List **10+ ideas** as one-liners (≤ 2 sentences each). No elaboration, no evaluation — quantity over quality.
2. Vary along these dimensions — if all your ideas cluster on one, force ideas on the others (these are starting dimensions, not exhaustive — add problem-specific dimensions as needed):
   - **Timing**: when does it happen? (before, during, after, periodic)
   - **Actor**: who/what does it? (agent, system, user, tool, separate process)
   - **Mechanism**: how is it enforced? (rule, example, tool, workflow step, system injection)
   - **Scope**: where does it apply? (per-item, per-task, per-session, global)
3. Review your list. Mark ideas that share the same core mechanism with the same letter (A, B, C...). If any group has >3 ideas, you are converging — force ideas using underrepresented mechanisms.

The only exception: if the change is purely mechanical (e.g., rewording a single phrase, moving text between sections), 5 ideas minimum.

**Example** (problem: agent does not use memory skill):
```
1. (A) Add rule: "after each important step, update memory" — agent-driven, during-work
2. (B) System injects <system-reminder> after each tool call — system-driven, periodic
3. (A) Add workflow step at end: "update memory with key findings" — agent-driven, after-work
4. (C) Script collects progress items, prompts agent to persist important ones — tool-enforced, periodic
5. (A) Rule deferred: only given at the workflow step that should trigger it — agent-driven, after-work
6. (D) Workflow step 1: drop stale items from prior agents — agent-driven, before-work
7. (B) Emit reminder only when agent produces output matching importance heuristic — system-driven, conditional
8. (E) User confirms which items to persist at end of session — user-driven, after-work
9. (C) Tool auto-persists anything written to a scratch file — tool-enforced, during-work
10. (F) Separate background agent monitors conversation, persists independently — separate process, periodic
```
Note: letters mark mechanism groups. Ideas 1/3/5 share mechanism (A), signaling convergence — ideas 7-10 were forced into underrepresented groups.

NEXT STEP:
<invoke working-dir="~/.claude/skills/scripts" cmd="python3 -m skills.prompt_patch.do --step 3 --ideas='...'" />
Execute this command now.

<!-- step 3: identify -->

# Prompt Patch - Identify Target State & Workflows

Define the target and generate multiple paths to reach it.

1. **Target result state**: Describe the exact end-state you want the agent to produce.
   (e.g., "all facts verified before inclusion", "code compiles and passes tests before response")

2. **Workflow options** Build your workflow options from ideas in your brainstorm list (step 2). Select ideas from different mechanism groups. You may combine or refine ideas, but each option must trace to at least one brainstorm idea. For each, describe the sequence of tool calls / chain-of-thought / agent behavior that would produce the target state as they appear in the agent context window.

   Format per option:
   ```
   Option A: [name] (from brainstorm ideas #N, #M)
   [step] -> [step] -> [step] -> end
   ```

   Options must differ in **temporal sequence** — the order in which observable state changes occur. "State" means external artifacts (files on disk, tool call results) or internal artifacts (chain-of-thought constructions, intermediate reasoning). A reader tracing the reasoning log should see different intermediate states at different points in time.

   For non-mechanical changes, apply this test: if you wrote out what happens at each moment for two options, would the sequences diverge? If not, the options are not distinct — revise.

   NOT distinct (same temporal sequence, different framing):
   - Same steps, different prompt section targeted
   - Same approach, one described as a loop and one as linear
   - Same workflow, different naming

   Distinct (different intermediate states over time):
   - A builds an intermediate artifact then transforms it; B writes the final form directly
   - A reads context first then drafts; B drafts then validates against context
   - A uses chain-of-thought to construct a decision tree then selects; B evaluates options sequentially

NEXT STEP:
<invoke working-dir="~/.claude/skills/scripts" cmd="python3 -m skills.prompt_patch.do --step 4 --target-state='...' --option-a='...' --option-b='...'" />
Execute this command now.

<!-- step 4: draft-options -->

# Prompt Patch - Draft Prompt Updates Per Option

For EACH workflow option from step 3, write the concrete set of prompt changes needed to make the agent follow that workflow.

Per option, specify:

- **Instructions to add/modify**: exact wording
- **Instructions to remove**: what existing text conflicts
- **Placement**: where in the prompt (system prompt section, CLAUDE.md, skill file, etc.)
- **Trigger condition**: when should this instruction activate

Do NOT pick a winner yet. Write both/all options fully.

NEXT STEP:
<invoke working-dir="~/.claude/skills/scripts" cmd="python3 -m skills.prompt_patch.do --step 5 --options-drafted='brief summary of each option'" />
Execute this command now.

<!-- step 5: context-check -->

# Prompt Patch - Context & Conflict Check

Check the existing instruction environment for alignment and conflicts.

1. **Read your system prompt** (use `docs/system-prompt-snapshot/` if available, or reason about your own behavior) and any CLAUDE.md / settings.json in context.

2. For each drafted option, answer:

   | Question | Answer |
   | --- | --- |
   | Which existing instructions **reinforce** this change? | ... |
   | Which existing instructions **contradict** this change? | ... |
   | What can go wrong at each step of this workflow? | ... |

3. **Revise** each option based on conflicts found. If a contradiction cannot be resolved, note it as a hard constraint.

NEXT STEP:
<invoke working-dir="~/.claude/skills/scripts" cmd="python3 -m skills.prompt_patch.do --step 6 --conflicts-found='...' --revisions-made='...'" />
Execute this command now.

<!-- step 6: regressions -->

# Prompt Patch - Regression Analysis

Your prompt changes will affect ALL invocations, not just the case you are optimizing for.

For each option:

1. **List 3+ scenarios** where the agent currently behaves correctly that your changes could break.
2. For each scenario, explain the regression mechanism (why would the change cause wrong behavior there?).
3. **Revise** the prompt changes to mitigate identified regressions. If mitigation is impossible, note the tradeoff.

Format:
```
Scenario: [description]
Current behavior: [correct behavior now]
Risk: [how your change breaks it]
Mitigation: [revised wording] or [accepted tradeoff: ...]
```

NEXT STEP:
<invoke working-dir="~/.claude/skills/scripts" cmd="python3 -m skills.prompt_patch.do --step 7 --regressions-found='...' --mitigations='...'" />
Execute this command now.

<!-- step 7: pick-draft -->

# Prompt Patch - Pick Best Option & Full Draft

1. **Pick the best option.** State why. Reference specific advantages over alternatives (from steps 4-6 analysis).

2. **Write the full draft** of all prompt changes. Include:
   - Complete text of every instruction added/modified/removed
   - Exact placement (file, section, position relative to existing content)
   - Any conditional logic or gating

Write the draft as it would appear in the final file -- not a summary, the actual text.

NEXT STEP:
<invoke working-dir="~/.claude/skills/scripts" cmd="python3 -m skills.prompt_patch.do --step 8 --chosen-option='...' --draft-written='yes'" />
Execute this command now.

<!-- step 8: deterministic-check -->

# Prompt Patch - Deterministic Failure Mode Check

Review your draft for failure modes that will reliably break:

1. **Commands that may crash or not run** in the runtime environment of the prompt:
   - Missing binaries, wrong paths, permission issues
   - **Special attention**: commands that silently return wrong results (exit 0 but wrong output, empty output treated as success)

2. **Impossible to follow** in certain situations:
   - Instructions that assume state/context that may not exist
   - Instructions that require tools/capabilities the agent may not have

3. **Impossible to know WHEN to follow**: "If X, do Y" where:
   - Checking X is not possible with available tools
   - How to check X is not specified
   - X is ambiguous or subjective without a decision procedure

For each issue found: **revise the draft**.

Then list **environment requirements** (e.g., "python3 needed", "git available", "internet access").
You may assume any requirement that is true in your current environment.

NEXT STEP:
<invoke working-dir="~/.claude/skills/scripts" cmd="python3 -m skills.prompt_patch.do --step 9 --deterministic-issues='...' --env-requirements='...'" />
Execute this command now.

<!-- step 9: non-deterministic-check -->

# Prompt Patch - Non-Deterministic Error Check

What mistakes may the agent make even with correct instructions?

Consider:

1. **Misinterpretation**: Instructions that could be read multiple ways. Ambiguous scope, unclear referents.
2. **Skipping**: Instructions the agent is likely to skip under pressure (long tasks, complex context, user urgency).
3. **Over-application**: Instructions the agent might apply too broadly (false positives on trigger conditions).
4. **Ordering errors**: Steps the agent might execute out of order or in parallel when sequential is required.
5. **Hallucination risks**: Points where the agent might fabricate rather than check (especially verification steps).

For each risk identified, assess severity (low/medium/high) and revise the draft if severity >= medium.

NEXT STEP:
<invoke working-dir="~/.claude/skills/scripts" cmd="python3 -m skills.prompt_patch.do --step 10 --risks-found='...' --revisions='...'" />
Execute this command now.

<!-- step 10: top-concerns -->

# Prompt Patch - Top Concerns

List your **3 top problems or concerns** about the proposed changes.

Focus on points NOT already covered by the previous steps (steps 5-9). These should be novel concerns -- things this workflow might have missed.

For each concern:
- **Problem**: What could go wrong?
- **Likelihood**: How likely is it? (low/medium/high)
- **Impact**: What is the consequence? (low/medium/high)
- **Possible mitigation**: Is there anything that can be done? (may be "none" or "accept risk")

If any concern has both likelihood >= medium AND impact >= medium, revise the draft to address it before proceeding.

NEXT STEP:
<invoke working-dir="~/.claude/skills/scripts" cmd="python3 -m skills.prompt_patch.do --step 11 --concerns='...' --final-revisions='...'" />
Execute this command now.

<!-- step 11: final -->

# Prompt Patch - Final Version

Write the **final version** of all prompt changes.

This is the deliverable. Include:

1. **For each file changed**: full path, and the complete change (add/modify/remove) with exact text
2. **Environment requirements** (from step 8)
3. **Known tradeoffs** (from steps 6, 10) -- accepted regressions or risks
4. **Testing suggestion**: one concrete way to verify the change works as intended

Present the changes so they can be applied directly (copy-paste ready or as diffs).

Done. Respond to the user with the final version.
