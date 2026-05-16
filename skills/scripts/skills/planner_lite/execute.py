#!/usr/bin/env python3
"""Planner-lite execute.py: 4-step execution workflow.

DeepThink pattern: STEPS dict, STEP_HANDLERS dict,
format_step_output(), WORKFLOW constant, argparse main().

No Task tool, no AskUserQuestion (subagent-compatible).
"""

import argparse
import sys
from pathlib import Path

from skills.lib.workflow.core import StepDef, Workflow
from skills.lib.workflow.ast import (
    StepHeaderNode, CurrentActionNode, InvokeAfterNode,
    render_step_header, render_current_action, render_invoke_after,
)


MODULE_PATH = "planner_lite.execute"
MAX_ITERATIONS = 3


def format_step_output(
    step: int,
    total: int,
    title: str,
    actions: list[str],
    next_command: str | None = None,
    is_step_zero: bool = False,
) -> str:
    """Format complete step output using AST builder API.

    Args:
        step: Current step number (1-indexed)
        total: Total steps
        title: Step title
        actions: List of action strings
        next_command: Command to invoke after (None = workflow complete)
        is_step_zero: If True, prepend XML mandate (for step 1)
    """
    parts = []
    parts.append(render_step_header(StepHeaderNode(title=title, script="execute", step=step)))
    parts.append("")

    if is_step_zero:
        parts.append("""<xml_format_mandate>
  All workflow output MUST be well-formed XML.
  Use CDATA for code: <![CDATA[...]]>
</xml_format_mandate>""")
        parts.append("")

    parts.append(render_current_action(CurrentActionNode(actions)))
    parts.append("")

    if next_command:
        parts.append(render_invoke_after(InvokeAfterNode(cmd=next_command)))
    elif step >= total:
        parts.append("WORKFLOW COMPLETE - All milestones implemented")

    return "\n".join(parts)


STEPS = {
    1: {
        "title": "Plan Analysis and Milestone Ordering",
        "actions": [
            "Read plan.md and context.json from state_dir.",
            "Analyze milestones and determine execution order.",
        ],
    },
    2: {
        "title": "Implementation",
        "actions": [
            "Implement milestone specified by --milestone arg.",
        ],
    },
    3: {
        "title": "Self-Review",
        "actions": [
            "Self-review implementation quality.",
        ],
    },
    4: {
        "title": "Completion and Summary",
        "actions": [
            "Output completion summary.",
        ],
    },
}


def get_step_1_output(args, step_info):
    """Plan Analysis and Milestone Ordering (step 1).

    Reads plan.md and context.json from state_dir. Context.json handover schema reuse
    (ref: DL-004) enables execute phase to access planning constraints without
    re-prompting. Plan.md as markdown state artifact (ref: DL-002) eliminates JSON IR
    parsing. Extracts milestones, outputs analysis instructions listing sequential
    execution order.

    Outputs invoke_after for first milestone's step 2.
    Exits non-zero if state_dir missing or plan.md/context.json unreadable.
    """
    state_dir = Path(args.state_dir)
    plan_path = state_dir / "plan.md"
    context_path = state_dir / "context.json"

    if not plan_path.exists():
        print(f"plan.md not found in {state_dir}", file=sys.stderr)
        sys.exit(1)

    if not context_path.exists():
        print(f"context.json not found in {state_dir}", file=sys.stderr)
        sys.exit(1)

    actions = [
        "You are implementing a plan stored in the state directory.",
        "",
        "PART A - READ STATE ARTIFACTS:",
        f"  Read plan.md from: {plan_path}",
        f"  Read context.json from: {context_path}",
        "",
        "PART B - ANALYZE MILESTONES:",
        "  Identify all milestones in the plan.",
        "  For each milestone, extract:",
        "  - Milestone identifier (e.g., M-001, M-002)",
        "  - Milestone title",
        "  - Files to be created or modified",
        "  - Acceptance criteria",
        "  - Code intents (detailed implementation instructions)",
        "",
        "PART C - DETERMINE EXECUTION ORDER:",
        "  List milestones in sequential execution order.",
        "  Milestones should be implemented one at a time.",
        "  Dependencies should be respected (earlier milestones may set up infrastructure for later ones).",
        "",
        "PART D - IDENTIFY FIRST MILESTONE:",
        "  Note the identifier of the first milestone to implement.",
        "",
        "OUTPUT FORMAT:",
        "```",
        "MILESTONES (in execution order):",
        "1. [identifier]: [title]",
        "   Files: [list]",
        "   Acceptance Criteria: [summary]",
        "",
        "2. [identifier]: [title]",
        "   Files: [list]",
        "   Acceptance Criteria: [summary]",
        "",
        "[...]",
        "",
        "FIRST MILESTONE: [identifier]",
        "```",
    ]

    # Assume first milestone is "1" or "M-001" - agent will determine actual identifier
    next_cmd = f"agent-tools skill {MODULE_PATH} --step 2 --state-dir {args.state_dir} --milestone 1"

    return format_step_output(
        step=args.step,
        total=len(STEPS),
        title=f"PLANNER-LITE - {step_info['title']}",
        actions=actions,
        next_command=next_cmd,
        is_step_zero=True,
    )


def get_step_2_output(args, step_info):
    """Implementation (step 2).

    Validates --milestone arg is provided. Reads plan.md to extract the specified
    milestone's details: code intents, file paths, acceptance criteria.
    Outputs detailed implementation instructions for the milestone.

    Outputs invoke_after for step 3 --iteration 1 (self-review).
    Exits non-zero if --milestone missing or milestone not found in plan.md.
    """
    if not args.milestone:
        print("--milestone required for step 2", file=sys.stderr)
        sys.exit(1)

    state_dir = Path(args.state_dir)
    plan_path = state_dir / "plan.md"

    if not plan_path.exists():
        print(f"plan.md not found in {state_dir}", file=sys.stderr)
        sys.exit(1)

    actions = [
        f"You are implementing milestone: {args.milestone}",
        "",
        "PART A - EXTRACT MILESTONE DETAILS:",
        f"  Read plan.md from: {plan_path}",
        f"  Locate milestone {args.milestone} section.",
        "  Extract:",
        "  - Files to create or modify (from **Files** section)",
        "  - Requirements (from **Requirements** section)",
        "  - Acceptance criteria (from **Acceptance Criteria** section)",
        "  - Code intents (from **Code Intent** section - these contain detailed implementation instructions)",
        "",
        "PART B - IMPLEMENTATION INSTRUCTIONS:",
        "  For each file in the milestone:",
        "  ",
        "  1. FILE PATH: Note the absolute path where the file should be created/modified",
        "  ",
        "  2. CODE INTENT: Extract the code intent for this file",
        "     Code intents are labeled with identifiers like CI-M-XXX-YYY",
        "     They contain detailed implementation instructions including:",
        "     - What the code should do",
        "     - Key patterns to follow",
        "     - Functions/classes to implement",
        "     - Error handling requirements",
        "  ",
        "  3. IMPLEMENTATION APPROACH:",
        "     - Follow the DeepThink pattern if specified",
        "     - Use the workflow AST library for step output formatting",
        "     - Follow existing codebase conventions",
        "     - Ensure imports are correct",
        "     - Add comprehensive error handling",
        "  ",
        "  4. ACCEPTANCE CRITERIA: Keep these in mind as implementation targets",
        "",
        "PART C - EXECUTE IMPLEMENTATION:",
        "  Implement ALL files for this milestone.",
        "  Use Read tool first if modifying existing files.",
        "  Use Edit or Write tools to create/modify files.",
        "  Ensure all code is complete and functional (no stubs or placeholders).",
        "",
        "IMPORTANT CONSTRAINTS:",
        "  - Do NOT use Task tool",
        "  - Do NOT use AskUserQuestion",
        "  - Implement code directly using Read/Write/Edit tools",
        "  - All step handlers must have fully detailed action text (not stubs)",
        "",
        "OUTPUT: Complete implementation of all files in the milestone.",
    ]

    next_cmd = f"agent-tools skill {MODULE_PATH} --step 3 --state-dir {args.state_dir} --milestone {args.milestone} --iteration 1"

    return format_step_output(
        step=args.step,
        total=len(STEPS),
        title=f"PLANNER-LITE - {step_info['title']} (Milestone {args.milestone})",
        actions=actions,
        next_command=next_cmd,
    )


def get_step_3_output(args, step_info):
    """Self-Review (step 3).

    Outputs self-review checklist with 4 items:
    (a) acceptance criteria from plan.md pass for current milestone
    (b) tests pass (if applicable)
    (c) implementation follows existing codebase patterns
    (d) no Task tool or AskUserQuestion introduced in any output

    If items fail and --iteration < MAX_ITERATIONS (3): invoke_after loops back to step 3 with iteration+1
    If items pass or --iteration >= MAX_ITERATIONS: output instructions to determine next milestone or proceed to step 4
    """
    iteration = args.iteration
    milestone = args.milestone

    state_dir = Path(args.state_dir)
    plan_path = state_dir / "plan.md"

    actions = [
        f"SELF-REVIEW - Milestone {milestone} (Iteration {iteration} of {MAX_ITERATIONS})",
        "",
        "Review the implementation you just completed against these criteria:",
        "",
        "CHECKLIST:",
        "",
        f"  (a) ACCEPTANCE CRITERIA: Read plan.md ({plan_path}) and verify that",
        f"      ALL acceptance criteria for milestone {milestone} are satisfied.",
        "      Use Read tool to check implemented files if needed.",
        "      List each criterion and whether it passes.",
        "",
        "  (b) TESTS: If the milestone specifies tests:",
        "      - Verify test files exist",
        "      - Run tests if possible (use Bash tool with pytest/unittest)",
        "      - Report test results",
        "      If no tests specified: mark as N/A",
        "",
        "  (c) CODEBASE PATTERNS: Verify implementation follows existing patterns:",
        "      - Import paths match existing code",
        "      - Error handling follows project conventions",
        "      - Code structure matches DeepThink pattern (if applicable)",
        "      - WORKFLOW constant is properly defined and discoverable",
        "",
        "  (d) PROHIBITED TOOLS: Verify that the implementation does NOT:",
        "      - Use Task tool",
        "      - Use AskUserQuestion tool",
        "      - These tools are not compatible with subagent execution",
        "",
        "OUTPUT FORMAT:",
        "```",
        "CHECKLIST RESULTS:",
        "(a) ACCEPTANCE CRITERIA: [PASS/FAIL]",
        "    - [criterion 1]: [pass/fail with details]",
        "    - [criterion 2]: [pass/fail with details]",
        "",
        "(b) TESTS: [PASS/FAIL/N/A]",
        "    [test results or N/A explanation]",
        "",
        "(c) CODEBASE PATTERNS: [PASS/FAIL]",
        "    [assessment with specific examples]",
        "",
        "(d) PROHIBITED TOOLS: [PASS/FAIL]",
        "    [confirmation or identified violations]",
        "",
        "OVERALL: [PASS/FAIL]",
        "```",
        "",
    ]

    if iteration >= MAX_ITERATIONS:
        actions.extend([
            f"ITERATION LIMIT REACHED ({MAX_ITERATIONS})",
            "Proceeding regardless of review results.",
            "",
            "NEXT STEPS:",
            "  Determine if there are more milestones to implement.",
            f"  Read plan.md ({plan_path}) to identify the next milestone after {milestone}.",
            "  ",
            "  If more milestones exist:",
            "    Note the next milestone identifier.",
            "  ",
            "  If all milestones are complete:",
            "    Proceed to completion summary.",
        ])
        # Agent will determine the actual next milestone or step 4
        next_cmd = f"agent-tools skill {MODULE_PATH} --step 4 --state-dir {args.state_dir}"
    else:
        actions.extend([
            "DECISION LOGIC:",
            "",
            "  IF OVERALL = FAIL:",
            "    - Identify specific issues",
            "    - Fix the issues",
            f"    - Invoke: agent-tools skill {MODULE_PATH} --step 3 --state-dir {args.state_dir} --milestone {milestone} --iteration {iteration + 1}",
            "",
            "  IF OVERALL = PASS:",
            "    - Determine if there are more milestones",
            f"    - Read plan.md ({plan_path}) to find the next milestone after {milestone}",
            "    - If more milestones: Invoke step 2 with next milestone identifier",
            "    - If all complete: Invoke step 4",
        ])
        # Provide both possible paths
        next_cmd_fail = f"agent-tools skill {MODULE_PATH} --step 3 --state-dir {args.state_dir} --milestone {milestone} --iteration {iteration + 1}"
        next_cmd_pass_next = f"agent-tools skill {MODULE_PATH} --step 2 --state-dir {args.state_dir} --milestone <next_milestone_id>"
        next_cmd_pass_done = f"agent-tools skill {MODULE_PATH} --step 4 --state-dir {args.state_dir}"
        next_cmd = f"If FAIL: {next_cmd_fail}\nIf PASS (more milestones): {next_cmd_pass_next}\nIf PASS (all complete): {next_cmd_pass_done}"

    return format_step_output(
        step=args.step,
        total=len(STEPS),
        title=f"PLANNER-LITE - {step_info['title']} (Milestone {milestone}, Iteration {iteration})",
        actions=actions,
        next_command=next_cmd,
    )


def get_step_4_output(args, step_info):
    """Completion and Summary (step 4).

    Outputs completion summary instructions: list milestones implemented, files modified.
    No invoke_after (workflow complete).
    """
    state_dir = Path(args.state_dir)
    plan_path = state_dir / "plan.md"

    actions = [
        "Implementation workflow complete.",
        "",
        "PART A - MILESTONES IMPLEMENTED:",
        f"  Read plan.md from: {plan_path}",
        "  List all milestones that were implemented.",
        "  For each milestone:",
        "  - Milestone identifier",
        "  - Milestone title",
        "  - Implementation status (completed/partial/skipped)",
        "",
        "PART B - FILES MODIFIED:",
        "  List all files that were created or modified during implementation.",
        "  Use absolute paths.",
        "  Group by milestone if helpful.",
        "",
        "PART C - SUMMARY:",
        "  Provide a brief summary of the implementation work:",
        "  - Total number of milestones implemented",
        "  - Total number of files created/modified",
        "  - Any notable challenges or decisions made",
        "",
        "PART D - NEXT STEPS (if applicable):",
        "  If there are any remaining tasks or follow-up items, note them here.",
        "  Examples:",
        "  - Manual testing recommended",
        "  - Documentation updates needed",
        "  - Additional milestones not yet implemented",
        "",
        "OUTPUT FORMAT:",
        "```",
        "IMPLEMENTATION SUMMARY",
        "",
        "MILESTONES IMPLEMENTED:",
        "1. [identifier]: [title] - [status]",
        "2. [identifier]: [title] - [status]",
        "",
        "FILES MODIFIED:",
        "- [absolute path] (created/modified)",
        "- [absolute path] (created/modified)",
        "",
        "SUMMARY:",
        "[Brief narrative summary]",
        "",
        "NEXT STEPS:",
        "- [item] (if any)",
        "```",
    ]

    return format_step_output(
        step=args.step,
        total=len(STEPS),
        title=f"PLANNER-LITE - {step_info['title']}",
        actions=actions,
        next_command=None,
    )


STEP_HANDLERS = {
    1: get_step_1_output,
    2: get_step_2_output,
    3: get_step_3_output,
    4: get_step_4_output,
}


WORKFLOW = Workflow(
    "planner-lite-execute",
    StepDef(id="plan_analysis", title="Plan Analysis and Milestone Ordering", actions=STEPS[1]["actions"]),
    StepDef(id="implementation", title="Implementation", actions=STEPS[2]["actions"]),
    StepDef(id="self_review", title="Self-Review", actions=STEPS[3]["actions"]),
    StepDef(id="completion", title="Completion and Summary", actions=STEPS[4]["actions"]),
)


def main():
    """Planner-lite execution workflow CLI.

    Parses args (--step required, --state-dir required, --milestone for step 2,
    --iteration default 1), validates step number and required args, invokes step
    handler, outputs XML to stdout.

    Error handling: exits non-zero if invalid step number, state_dir missing, plan.md
    or context.json missing/unreadable, invalid milestone value. Specific errors:
    invalid step prints usage, missing state_dir prints '--state-dir required',
    missing milestone on step 2 prints '--milestone required for step 2',
    milestone not found prints 'milestone <id> not found in plan.md'.

    Step 2 requires --milestone arg to specify which milestone to implement.
    Agent iterates step 2->3 per milestone sequentially: single agent cannot parallelize
    milestone implementation, so execution proceeds one milestone at a time (ref: DL-002).

    Self-review iteration (step 3) limited to MAX_ITERATIONS=3 (ref: DL-003).
    """
    parser = argparse.ArgumentParser(
        description="Planner-lite execution workflow",
        epilog="Steps: 1 (Plan Analysis), 2 (Implementation), 3 (Self-Review), 4 (Completion)",
    )
    parser.add_argument("--step", type=int, required=True, help="Step number (1-4)")
    parser.add_argument("--state-dir", type=str, required=True, help="State directory containing plan.md and context.json")
    parser.add_argument("--milestone", type=str, help="Milestone identifier (required for step 2)")
    parser.add_argument("--iteration", type=int, default=1, help="Self-review iteration (for step 3)")

    args = parser.parse_args()

    # Validate state_dir
    if not args.state_dir:
        print("--state-dir required", file=sys.stderr)
        sys.exit(1)

    # Validate step
    if args.step < 1 or args.step > len(STEPS):
        print(f"Invalid step number: {args.step}. Valid steps: 1-{len(STEPS)}", file=sys.stderr)
        parser.print_help(sys.stderr)
        sys.exit(1)

    step_info = STEPS.get(args.step)
    if not step_info:
        print(f"Invalid step: {args.step}", file=sys.stderr)
        sys.exit(1)

    handler = STEP_HANDLERS.get(args.step)
    if not handler:
        print(f"No handler for step {args.step}", file=sys.stderr)
        sys.exit(1)

    output = handler(args, step_info)
    print(output)


if __name__ == "__main__":
    main()
