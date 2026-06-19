<!-- step 1: motivation -->

# Patch Mode - Motivation

The principles to keep in mind for this work live in this skill's `SKILL.md` (autoloaded). Re-read them now if they are not fresh in your context. The steps below operationalize the "fix invariants, not symptoms" rule against the specific prompt you are modifying.

Why make this change? What goes wrong if we do nothing?

Write out:

1. **The problem**: What specific behavior needs to change? Be concrete (quote output, describe failure mode, show example).
2. **Cost of inaction**: What happens if no prompt change is made? Who is affected and how?
3. **Success criteria**: How will you know the change worked? What observable difference?
4. **Classification**: Pick one mode. This gates Step 2 behavior.
   - `correctness` — a structural invariant is currently broken (or missing entirely; "adding a new capability" counts as correctness with structural gap = "invariant missing"). Step 2 will find the broken/missing pair.
   - `efficiency` — all invariants hold; you are optimizing within them (tokens, time, steps). Step 2 will enumerate invariants at risk during your optimization so Step 7 can preserve them.
   - `n/a (mechanical)` — typo, rename, or pure reordering with no behavioral change. Step 2 will short-circuit.

   If uncertain, default to `correctness`; you can re-run Step 1 if Step 2 finds no broken pair.

NEXT STEP:
<invoke cmd="agent-tools skill prompt_engineer_v2.do --step 2 <<'EOF'
## problem
...

## cost
...

## success-criteria
...

## mode
correctness|efficiency|n/a
EOF
" />
Execute this command now.

<!-- step 2: invariant-extraction -->

# Patch Mode - Invariant Extraction

Identify the (property, enforcement) pairs the target prompt/workflow guarantees.

If Step 1 mode is `n/a (mechanical)` — write "Mechanical change — no invariant analysis needed" and proceed to step 3.

**Invariants are structural properties paired with the enforcement mechanism that holds them.** LLMs are stochastic — instructions influence behavior probabilistically, not deterministically; the enforcement mechanism is what makes the property real.

**Useful invariants reject Step 4 design options; useless ones don't.** The common failure mode is *artifact-existence claims* ("a block appears in the response", "a tool call happens before reply", "the schema is defined in one place"); any Step 4 option that emits the named artifact passes the check, including options that emit the artifact in a position or context where it no longer enforces anything. Useful invariants describe *relationships between steps* — orderings ("commit written before rules reach context"), feedback loops ("violation found at checkpoint triggers restart"), asymmetric incentives ("no work-savings from under-reporting because the work is already done by the time the check fires"), dependency chains. After writing each pair, run the **sketch test**: imagine a Step 4 option that minimally emits the named artifact / makes the named tool call but otherwise behaves naively. If your sketch satisfies the pair while the underlying property silently breaks, the pair is artifact-existence — re-state it as the relationship the artifact was supposed to enforce, then re-run the sketch test on the new pair. (See First Principle #4 for worked examples.)

1. **List invariants as (property, enforcement) pairs.** 3-7 pairs.

   Format each pair:
   - **Invariant**: `<structural property>`
   - **Enforced by**: `<concrete artifact in the workflow — a step, a tool call, a fixed-format check>`. NOT "the agent does X" — that is a deterministic-instruction claim, not an enforcement. Enforcement must quote or reference specific text/step/tool in the target workflow, not paraphrase.

   Examples:
   - Invariant: "Workflow has no single point of failure."
     Enforced by: "Final output must pass 3 parallel runs of the reviewer at the same time before acceptance."
   - Invariant: "Iterative improvement converges — no candidate beats the chosen solution at termination."
     Enforced by: "Each iteration drafts ≥2 options and the prior winner is always one of them."
   - Invariant: "Any bug introduced has nonzero probability of discovery on subsequent tasks."
     Enforced by: "Each task starts with a regression-test pass over a rolling buffer of prior tasks."
   - Invariant: "Errors from tooling propagate to the user at least 50% of the time."
     Enforced by: "Stderr is not suppressed; commands that exit 0 with empty stdout are flagged."

   These examples illustrate the pair shape. Your target prompt's invariants must be specific to that prompt — do not reuse the example pairs verbatim.

   NOT invariants (deterministic-instruction claims, or properties without concrete enforcement):
   - "Agent will include string X in output because instruction Y says to."
   - "Agent reads section 3 then executes step Z."
   - "Agent always verifies because the prompt says IMPORTANT."

   A **review pair** is one whose enforcement mechanism is itself a check/test/review step. The TDD-for-prompts rule (First Principle #5) applies when the broken pair is a review pair.

2. **Branch on Step 1 mode**:

   - **correctness**: identify which pair is *currently broken* — its enforcement mechanism fails to hold the property. If the goal is to *add* a missing invariant, the broken pair is the would-be pair (its enforcement is absent). If the goal is to *remove* an over-aggressive enforcement, list the pair as it currently exists and explain in the next item why it's unwanted.

   - **efficiency**: identify which pairs are *at risk* during your optimization (e.g., shorter prompt risks dropping the enforcement for pair K). These must be preserved; Step 7 regression analysis will revisit them.

3. **Structural gap or risk**:

   - In correctness mode: which pair is broken/missing/to-remove, and what specifically about the workflow design lets that be the case? Describe the system-design gap with reference to specific workflow elements (step names, tool calls, or quoted prompt text) — not an execution trace.
   - In efficiency mode: for each at-risk pair, name the concrete enforcement mechanism that your optimization threatens (e.g., "Step 7 currently enforces pair K via 3-scenario regression list; collapsing Steps 6-7 would remove this enforcement").

NEXT STEP:
<invoke cmd="agent-tools skill prompt_engineer_v2.do --step 3 <<'EOF'
## invariants
...

## structural-gap
...

## mode
correctness|efficiency
EOF
" />
Execute this command now.

<!-- step 3: brainstorm -->

# Patch Mode - Brainstorm

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
<invoke cmd="agent-tools skill prompt_engineer_v2.do --step 4 <<'EOF'
## ideas
...
EOF
" />
Execute this command now.

<!-- step 4: identify -->

# Patch Mode - Identify Target State & Workflows

Define the target and generate multiple paths to reach it.

1. **Target result state**: Describe the exact end-state you want the agent to produce.
   (e.g., "all facts verified before inclusion", "code compiles and passes tests before response")

2. **Workflow options** Build your workflow options from ideas in your brainstorm list (step 3). Select ideas from different mechanism groups. You may combine or refine ideas, but each option must trace to at least one brainstorm idea. For each, describe the sequence of tool calls / chain-of-thought / agent behavior that would produce the target state as they appear in the agent context window.

   Format per option:
   ```
   Option A: [name] (from brainstorm ideas #N, #M)
   [step] -> [step] -> [step] -> end
   Structural invariants restored: [which structural properties from step 2 this option restores]
   Structural invariants abandoned: [which properties this option does NOT restore, and why that's acceptable]
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
<invoke cmd="agent-tools skill prompt_engineer_v2.do --step 5 <<'EOF'
## target-state
...

## option-a
...

## option-b
...
EOF
" />
Execute this command now.

<!-- step 5: draft-options -->

# Patch Mode - Draft Prompt Updates Per Option

For EACH workflow option from step 4, write the concrete set of prompt changes needed to make the agent follow that workflow.

Per option, specify:

- **Instructions to add/modify**: exact wording
- **Instructions to remove**: what existing text conflicts
- **Placement**: where in the prompt (system prompt section, CLAUDE.md, skill file, etc.)
- **Trigger condition**: when should this instruction activate

Do NOT pick a winner yet. Write both/all options fully.

NEXT STEP:
<invoke cmd="agent-tools skill prompt_engineer_v2.do --step 6 <<'EOF'
## options-drafted
brief summary of each option
EOF
" />
Execute this command now.

<!-- step 6: context-check -->

# Patch Mode - Context & Conflict Check

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
<invoke cmd="agent-tools skill prompt_engineer_v2.do --step 7 <<'EOF'
## conflicts-found
...

## revisions-made
...
EOF
" />
Execute this command now.

<!-- step 7: regressions -->

# Patch Mode - Regression Analysis

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
<invoke cmd="agent-tools skill prompt_engineer_v2.do --step 8 <<'EOF'
## regressions-found
...

## mitigations
...
EOF
" />
Execute this command now.

<!-- step 8: pick-draft -->

# Patch Mode - Pick Best Option & Full Draft

1. **Pick the best option.** State why. Reference specific advantages over alternatives (from steps 5-7 analysis).

2. **Write the full draft** of all prompt changes. Include:
   - Complete text of every instruction added/modified/removed
   - Exact placement (file, section, position relative to existing content)
   - Any conditional logic or gating

Write the draft as it would appear in the final file -- not a summary, the actual text.

NEXT STEP:
<invoke cmd="agent-tools skill prompt_engineer_v2.do --step 9 <<'EOF'
## chosen-option
...

## draft-written
yes
EOF
" />
Execute this command now.

<!-- step 9: deterministic-check -->

# Patch Mode - Deterministic Failure Mode Check

A "Deterministic Failure Mode" is one where a failure still occurs even if agent appears to follow instructions perfectly.

Review your draft for failure modes including but not limited to:

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

4. **Underspecified spec**
   - Possible things agent may do at a point in timeline that you consider "wrong/worse" than your inteneded behavior but is a better or equally resonable thing to do given the prompt and context they have at the point

5. **Missing context**
   - Your planned timeline does not provide a particular piece of context, or provide it too late -- agent must have the context at the point they need it

For each issue found: **revise the draft**.

Then list **prompt assumptions** (e.g., "python3 needed", "git available", "internet access", "Task is not review-only").
You may assume any requirement that is true in your current environment and task assumptions aligned with user goals and is clearly checkable from query.

NEXT STEP:
<invoke cmd="agent-tools skill prompt_engineer_v2.do --step 10 <<'EOF'
## deterministic-issues
...

## env-requirements
...
EOF
" />
Execute this command now.

<!-- step 10: non-deterministic-check -->

# Patch Mode - Non-Deterministic Error Check

What mistakes may the agent make even with correct instructions?

Consider:

1. **Misinterpretation**: Instructions that could be read multiple ways. Ambiguous scope, unclear referents.
2. **Skipping**: Instructions the agent is likely to skip under pressure (long tasks, complex context, user urgency).
3. **Over-application**: Instructions the agent might apply too broadly (false positives on trigger conditions).
4. **Ordering errors**: Steps the agent might execute out of order or in parallel when sequential is required.
5. **Hallucination risks**: Points where the agent might fabricate rather than check (especially verification steps).

For each risk identified, assess severity (low/medium/high) and revise the draft if severity >= medium.

NEXT STEP:
<invoke cmd="agent-tools skill prompt_engineer_v2.do --step 11 <<'EOF'
## risks-found
...

## revisions
...
EOF
" />
Execute this command now.

<!-- step 11: top-concerns -->

# Patch Mode - Top Concerns

List your **3 top problems or concerns** about the proposed changes.

Focus on points NOT already covered by the previous steps (steps 6-10). These should be novel concerns -- things this workflow might have missed.

For each concern:
- **Problem**: What could go wrong?
- **Likelihood**: How likely is it? (low/medium/high)
- **Impact**: What is the consequence? (low/medium/high)
- **Possible mitigation**: Is there anything that can be done? (may be "none" or "accept risk")

If any concern has both likelihood >= medium AND impact >= medium, revise the draft to address it before proceeding.

NEXT STEP:
<invoke cmd="agent-tools skill prompt_engineer_v2.do --step 12 <<'EOF'
## concerns
...

## final-revisions
...
EOF
" />
Execute this command now.

<!-- step 12: final -->

# Patch Mode - Final Version

Write the **final version** of all prompt changes.

This is the deliverable. Include:

1. **For each file changed**: full path, and the complete change (add/modify/remove) with exact text
2. **Environment requirements** (from step 9)
3. **Known tradeoffs** (from steps 7, 11) -- accepted regressions or risks
4. **Testing suggestion**: one concrete way to verify the change works as intended

Present the changes so they can be applied directly (copy-paste ready or as diffs).

Done. Respond to the user with the final version.
