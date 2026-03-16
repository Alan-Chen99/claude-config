#!/usr/bin/env python3
"""
Planner-lite Skill - Lightweight planning without subagent dispatch.

Four-step workflow:
  1. Context Capture and Exploration - Capture task spec, constraints, entry points
  2. Approach Generation and Decisions - Explore entry points, generate approach, create decision log
  3. Milestone Definition and Plan Writing - Define milestones with acceptance criteria, write plan.md
  4. Self-Review - Self-review checklist with iteration loop
"""

import argparse
import json
import sys
import tempfile
from pathlib import Path

from skills.lib.workflow.core import StepDef, Workflow
from skills.lib.workflow.ast import (
    StepHeaderNode, CurrentActionNode, InvokeAfterNode,
    render_step_header, render_current_action, render_invoke_after,
)


MAX_ITERATIONS = 3
MODULE_PATH = "skills.planner_lite.plan"


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

    # Step header
    parts.append(render_step_header(StepHeaderNode(title=title, script="planner-lite", step=step)))
    parts.append("")

    # XML mandate for step 1 (first step)
    if is_step_zero:
        parts.append("""<xml_format_mandate>
CRITICAL: All script outputs use XML format. You MUST:

1. Execute the action in <current_action>
2. When complete, invoke the exact command in <invoke_after>
3. The <next> block re-states the command -- execute it
4. For branching <invoke_after>, choose based on outcome:
   - <if_pass>: Use when action succeeded / QR returned PASS
   - <if_fail>: Use when action failed / QR returned ISSUES

DO NOT modify commands. DO NOT skip steps. DO NOT interpret.
</xml_format_mandate>""")
        parts.append("")

    # Current action
    parts.append(render_current_action(CurrentActionNode(actions)))
    parts.append("")

    # Invoke after or complete
    if next_command:
        parts.append(render_invoke_after(InvokeAfterNode(cmd=next_command)))
    elif step >= total:
        parts.append("WORKFLOW COMPLETE - Present results to user.")

    return "\n".join(parts)


STEPS = {
    1: {
        "title": "Context Capture and Exploration",
        "actions": [
            "You are an expert planner tasked with systematic task decomposition.",
            "",
            "PART A - TASK SPECIFICATION:",
            "  Review the user's request and the conversation history.",
            "  Extract the task specification, including:",
            "  - What needs to be built or changed",
            "  - Any explicit requirements or constraints",
            "  - Success criteria if stated",
            "",
            "PART B - CONSTRAINTS:",
            "  Identify constraints that will shape the implementation:",
            "  - Technical: language version, library compatibility, existing patterns",
            "  - Organizational: timeline, approval requirements",
            "  - Dependencies: external services, data formats",
            "",
            "PART C - ENTRY POINT EXPLORATION:",
            "  Identify starting points for implementation:",
            "  - Files that will need to change",
            "  - New files that will need to be created",
            "  - Existing patterns to follow",
            "  ",
            "  Use Read/Glob/Grep tools to explore the codebase:",
            "  - Find similar implementations",
            "  - Identify existing conventions",
            "  - Locate relevant documentation",
            "",
            "PART D - CURRENT UNDERSTANDING:",
            "  Based on exploration, summarize your current understanding:",
            "  - How the existing system works",
            "  - Where the new functionality fits",
            "  - What needs to change or be added",
            "",
            "PART E - ASSUMPTIONS:",
            "  List assumptions about the task:",
            "  - Interpretations of ambiguous requirements",
            "  - Default behaviors when not specified",
            "  - Scope boundaries",
            "",
            "PART F - INVISIBLE KNOWLEDGE:",
            "  Identify knowledge that won't be obvious from code alone:",
            "  - Why certain design decisions are necessary",
            "  - Architectural constraints or invariants",
            "  - Performance characteristics",
            "  - Business rules",
            "",
            "PART G - REFERENCE DOCUMENTATION:",
            "  Note any reference documentation discovered:",
            "  - CLAUDE.md files",
            "  - README.md files",
            "  - Existing patterns to follow",
            "  - API documentation",
            "",
            "PART H - WRITE CONTEXT FILE:",
            "  Write context.json to the state directory with this schema:",
            "  {",
            '    "task_spec": [list of task specification items],',
            '    "constraints": [list of constraints],',
            '    "entry_points": [list of entry point files/patterns],',
            '    "rejected_alternatives": [],  // Will be populated in step 2',
            '    "current_understanding": [list of understanding items],',
            '    "assumptions": [list of assumptions],',
            '    "invisible_knowledge": [list of invisible knowledge items],',
            '    "reference_docs": [list of reference documentation paths]',
            "  }",
            "",
            "OUTPUT FORMAT:",
            "```",
            "TASK SPECIFICATION:",
            "- [item 1]",
            "- [item 2]",
            "",
            "CONSTRAINTS:",
            "- [constraint 1]",
            "",
            "ENTRY POINTS:",
            "- [file/pattern 1]",
            "",
            "CURRENT UNDERSTANDING:",
            "- [understanding 1]",
            "",
            "ASSUMPTIONS:",
            "- [assumption 1]",
            "",
            "INVISIBLE KNOWLEDGE:",
            "- [knowledge 1]",
            "",
            "REFERENCE DOCUMENTATION:",
            "- [doc path 1]",
            "",
            "STATE DIRECTORY: [path where context.json was written]",
            "```",
        ],
    },
    2: {
        "title": "Approach Generation and Decisions",
        "actions": [
            "Based on the context captured in step 1, generate an implementation approach.",
            "",
            "PART A - APPROACH EXPLORATION:",
            "  Explore the entry points identified in context.json:",
            "  - Read relevant files to understand existing patterns",
            "  - Identify extension points",
            "  - Understand data flow and control flow",
            "",
            "  Use Read/Glob/Grep tools as needed to deepen understanding.",
            "",
            "PART B - APPROACH GENERATION:",
            "  Based on exploration, propose an implementation approach:",
            "  - High-level strategy",
            "  - Key components to create or modify",
            "  - Integration points with existing code",
            "  - Data structures and algorithms",
            "",
            "PART C - DECISION LOG:",
            "  For each significant decision in your approach, create a decision log entry.",
            "  Each entry MUST have:",
            "  - Decision: What you decided",
            "  - Reasoning Chain: At least 2 reasoning steps showing premise -> implication -> conclusion",
            "",
            "  INSUFFICIENT: 'Use JSON for config | JSON is standard'",
            "  SUFFICIENT: 'Use JSON for config | Need machine-readable format -> JSON has stdlib support -> Avoids external dependencies'",
            "",
            "  Include BOTH architectural and implementation-level decisions:",
            "  - Architectural: Module boundaries, data flow, component relationships",
            "  - Implementation: Specific algorithms, data structures, error handling strategies",
            "",
            "PART D - ALTERNATIVE APPROACHES:",
            "  Identify alternatives you considered but rejected:",
            "  - What was the alternative?",
            "  - Why was it rejected? (Be specific: performance, complexity, doesn't fit constraints)",
            "",
            "PART E - UPDATE CONTEXT FILE:",
            "  Update context.json with rejected alternatives:",
            "  - Read existing context.json",
            "  - Add rejected alternatives to the 'rejected_alternatives' list",
            "  - Write updated context.json back to state directory",
            "",
            "OUTPUT FORMAT:",
            "```",
            "APPROACH:",
            "[High-level strategy]",
            "",
            "KEY COMPONENTS:",
            "- [component 1]",
            "- [component 2]",
            "",
            "DECISION LOG:",
            "| Decision | Reasoning Chain |",
            "|----------|----------------|",
            "| [decision 1] | [step 1 -> step 2 -> conclusion] |",
            "| [decision 2] | [step 1 -> step 2 -> conclusion] |",
            "",
            "REJECTED ALTERNATIVES:",
            "| Alternative | Why Rejected |",
            "|------------|--------------|",
            "| [alt 1] | [concrete reason] |",
            "",
            "UPDATED: context.json with rejected alternatives",
            "```",
        ],
    },
    3: {
        "title": "Milestone Definition and Plan Writing",
        "actions": [
            "Based on the approach from step 2, define milestones and write the plan.",
            "",
            "PART A - MILESTONE DECOMPOSITION:",
            "  Break the implementation into milestones:",
            "  - Each milestone should be independently testable",
            "  - Dependencies should be clear (milestone X before milestone Y)",
            "  - Each milestone should have clear acceptance criteria",
            "",
            "PART B - MILESTONE DEFINITION:",
            "  For each milestone, define:",
            "  1. Name: Clear, descriptive name",
            "  2. Files: Exact paths to files created or modified",
            "  3. Requirements: Specific, testable requirements",
            "  4. Acceptance Criteria: Pass/fail criteria for completion",
            "  5. Code Intent: Behavior specification (not implementation diffs)",
            "",
            "  CODE INTENT GUIDELINES:",
            "  - Describe WHAT the code should do, not HOW (no diffs)",
            "  - Specify behavior, inputs, outputs, error handling",
            "  - Include function signatures and module exports",
            "  - Describe patterns to follow from existing code",
            "",
            "PART C - PLAN.MD STRUCTURE:",
            "  Write plan.md to the state directory using this structure:",
            "",
            "  # [Plan Title]",
            "",
            "  ## Overview",
            "  [Problem statement, chosen approach, key decisions in 1-2 paragraphs]",
            "",
            "  ## Planning Context",
            "",
            "  ### Decision Log",
            "  [Table from step 2 with Decision | Reasoning Chain columns]",
            "",
            "  ### Rejected Alternatives",
            "  [Table from step 2 with Alternative | Why Rejected columns]",
            "",
            "  ### Constraints & Assumptions",
            "  [List from context.json]",
            "",
            "  ### Known Risks",
            "  [Table with Risk | Mitigation | Anchor columns]",
            "  [If claiming existing code behavior, cite file:line anchors]",
            "",
            "  ## Invisible Knowledge",
            "",
            "  [Knowledge from context.json that won't be obvious from code]",
            "",
            "  ### Architecture",
            "  [ASCII diagram showing component relationships if applicable]",
            "",
            "  ### Why This Structure",
            "  [Reasoning behind module organization]",
            "",
            "  ### Invariants",
            "  [Rules that must be maintained but aren't enforced by code]",
            "",
            "  ### Tradeoffs",
            "  [Key decisions with costs and benefits]",
            "",
            "  ## Milestones",
            "",
            "  ### Milestone 1: [Name]",
            "",
            "  **Files**: [exact paths]",
            "",
            "  **Requirements**:",
            "  - [specific requirement 1]",
            "  - [specific requirement 2]",
            "",
            "  **Acceptance Criteria**:",
            "  - [testable criterion 1]",
            "  - [testable criterion 2]",
            "",
            "  **Code Intent**:",
            "  - [behavior specification 1]",
            "  - [behavior specification 2]",
            "",
            "  [Repeat for each milestone]",
            "",
            "PART D - EXCLUSIONS:",
            "  Note: The following sections are NOT included in lite mode:",
            "  - Code Changes (diffs) - requires multi-agent separation (DL-006)",
            "  - Diagram IR - requires multi-agent separation (DL-006)",
            "  - Tests section - tests are described in Code Intent",
            "",
            "PART E - WRITE PLAN:",
            "  Write plan.md to the state directory following the structure above.",
            "  Ensure all sections are populated from context.json and step 2 outputs.",
            "",
            "OUTPUT FORMAT:",
            "```",
            "MILESTONES DEFINED:",
            "1. [Milestone 1 name] - [brief description]",
            "2. [Milestone 2 name] - [brief description]",
            "[...]",
            "",
            "PLAN WRITTEN: [state_dir]/plan.md",
            "",
            "PLAN SUMMARY:",
            "- Total milestones: [N]",
            "- Decision log entries: [N]",
            "- Rejected alternatives: [N]",
            "- Known risks: [N]",
            "```",
        ],
    },
    4: {
        "title": "Self-Review",
        "actions": [],  # Generated dynamically based on iteration
    },
}


def get_step_4_actions(iteration: int) -> list[str]:
    """Generate step 4 actions dynamically based on iteration."""
    actions = [
        f"ITERATION {iteration} OF {MAX_ITERATIONS}",
        "",
        "Review the plan.md file from step 3 against quality criteria.",
        "",
        "PART A - REVIEW CHECKLIST:",
        "  Review each item. Mark as PASS or FAIL with specific findings.",
        "",
        "  (a) ACCEPTANCE CRITERIA:",
        "      Every milestone has testable pass/fail acceptance criteria.",
        "      BAD: 'Works correctly', 'Handles errors properly'",
        "      GOOD: 'Returns 429 after 3 failed attempts', 'Parses all valid inputs'",
        "",
        "  (b) DECISION LOG:",
        "      Every decision log entry has 2+ reasoning steps.",
        "      BAD: 'Use JSON | JSON is standard'",
        "      GOOD: 'Use JSON | Need machine-readable format -> JSON has stdlib support -> Avoids dependencies'",
        "",
        "  (c) CONSTRAINTS:",
        "      All constraints from context.json are addressed in the plan.",
        "      If a constraint is explicitly deviated from, rationale is provided.",
        "",
        "  (d) PLAN.MD EXISTS:",
        "      plan.md exists in state directory with all required sections:",
        "      - Overview",
        "      - Decision Log",
        "      - Rejected Alternatives",
        "      - Constraints & Assumptions",
        "      - Known Risks",
        "      - Invisible Knowledge",
        "      - Milestones",
        "",
        "  (e) CODE INTENTS:",
        "      Code intents specify behavior not implementation diffs.",
        "      BAD: 'Add line 42: def foo()', 'Change variable name from x to y'",
        "      GOOD: 'Function foo(input) validates input and returns result', 'Module exports Workflow class'",
        "",
        "PART B - FINDINGS:",
        "  For each checklist item, provide specific findings:",
        "  - PASS: Item meets criteria",
        "  - FAIL: Item does not meet criteria [specific issue]",
        "",
        "PART C - REVISION (if needed):",
        "  If any items FAIL:",
        "  - Read plan.md",
        "  - Make specific corrections addressing the failures",
        "  - Write updated plan.md back to state directory",
        "  - Document what was changed",
        "",
    ]

    if iteration < MAX_ITERATIONS:
        actions.extend([
            "PART D - ITERATION DECISION:",
            "  If ALL items PASS: Workflow complete",
            f"  If ANY items FAIL and iteration < {MAX_ITERATIONS}: Continue to next iteration",
            "",
            "OUTPUT FORMAT:",
            "```",
            "REVIEW FINDINGS:",
            "(a) Acceptance Criteria: [PASS | FAIL: specific issue]",
            "(b) Decision Log: [PASS | FAIL: specific issue]",
            "(c) Constraints: [PASS | FAIL: specific issue]",
            "(d) plan.md Exists: [PASS | FAIL: specific issue]",
            "(e) Code Intents: [PASS | FAIL: specific issue]",
            "",
            "REVISIONS MADE (if any):",
            "- [change 1]",
            "- [change 2]",
            "",
            "DECISION: [COMPLETE | CONTINUE]",
            "```",
        ])
    else:
        actions.extend([
            "PART D - FINAL ITERATION:",
            f"  This is iteration {MAX_ITERATIONS} (final iteration).",
            "  Workflow will complete after this iteration regardless of findings.",
            "",
            "OUTPUT FORMAT:",
            "```",
            "FINAL REVIEW FINDINGS:",
            "(a) Acceptance Criteria: [PASS | FAIL: specific issue]",
            "(b) Decision Log: [PASS | FAIL: specific issue]",
            "(c) Constraints: [PASS | FAIL: specific issue]",
            "(d) plan.md Exists: [PASS | FAIL: specific issue]",
            "(e) Code Intents: [PASS | FAIL: specific issue]",
            "",
            "REVISIONS MADE (if any):",
            "- [change 1]",
            "- [change 2]",
            "",
            f"DECISION: COMPLETE (final iteration {MAX_ITERATIONS})",
            "```",
        ])

    return actions


def get_step_1_output(_args, step_info):
    """Handle Step 1: Context Capture and Exploration."""
    # Create state directory
    try:
        state_dir = tempfile.mkdtemp(prefix="planner-lite-")
    except OSError as e:
        print(f"ERROR: Cannot create state directory: {e}", file=sys.stderr)
        sys.exit(1)

    actions = list(step_info["actions"])
    # Insert state directory path into actions
    actions = [a.replace("[path where context.json was written]", state_dir) for a in actions]

    next_cmd = f"python3 -m {MODULE_PATH} --step 2 --state-dir {state_dir}"
    return format_step_output(
        step=1,
        total=4,
        title=f"PLANNER-LITE - {step_info['title']}",
        actions=actions,
        next_command=next_cmd,
        is_step_zero=True,
    )


def get_step_2_output(args, step_info):
    """Handle Step 2: Approach Generation and Decisions."""
    # Validate state_dir exists
    if not args.state_dir:
        sys.exit("ERROR: --state-dir required for step 2")

    state_dir = args.state_dir
    context_file = Path(state_dir) / "context.json"

    if not context_file.exists():
        sys.exit(f"ERROR: context.json not found in {state_dir}")

    # Validate context.json is parseable
    try:
        with open(context_file) as f:
            json.load(f)
    except json.JSONDecodeError as e:
        sys.exit(f"ERROR: context.json malformed: {e}")

    actions = list(step_info["actions"])
    next_cmd = f"python3 -m {MODULE_PATH} --step 3 --state-dir {state_dir}"

    return format_step_output(
        step=2,
        total=4,
        title=f"PLANNER-LITE - {step_info['title']}",
        actions=actions,
        next_command=next_cmd,
    )


def get_step_3_output(args, step_info):
    """Handle Step 3: Milestone Definition and Plan Writing."""
    # Validate state_dir exists
    if not args.state_dir:
        sys.exit("ERROR: --state-dir required for step 3")

    state_dir = args.state_dir
    context_file = Path(state_dir) / "context.json"

    if not context_file.exists():
        sys.exit(f"ERROR: context.json not found in {state_dir}")

    # Validate context.json is parseable
    try:
        with open(context_file) as f:
            json.load(f)
    except json.JSONDecodeError as e:
        sys.exit(f"ERROR: context.json malformed: {e}")

    actions = list(step_info["actions"])
    next_cmd = f"python3 -m {MODULE_PATH} --step 4 --state-dir {state_dir} --iteration 1"

    return format_step_output(
        step=3,
        total=4,
        title=f"PLANNER-LITE - {step_info['title']}",
        actions=actions,
        next_command=next_cmd,
    )


def get_step_4_output(args, step_info):
    """Handle Step 4: Self-Review."""
    # Validate state_dir exists
    if not args.state_dir:
        sys.exit("ERROR: --state-dir required for step 4")

    state_dir = args.state_dir
    plan_file = Path(state_dir) / "plan.md"

    if not plan_file.exists():
        sys.exit(f"ERROR: plan.md not found in {state_dir}")

    actions = get_step_4_actions(args.iteration)

    # Determine next command based on iteration
    if args.iteration < MAX_ITERATIONS:
        next_cmd = f"python3 -m {MODULE_PATH} --step 4 --state-dir {state_dir} --iteration {args.iteration + 1}"
    else:
        next_cmd = None  # Workflow complete

    return format_step_output(
        step=4,
        total=4,
        title=f"PLANNER-LITE - {step_info['title']} (Iteration {args.iteration})",
        actions=actions,
        next_command=next_cmd,
    )


STEP_HANDLERS = {
    1: get_step_1_output,
    2: get_step_2_output,
    3: get_step_3_output,
    4: get_step_4_output,
}


# Workflow definition for test framework auto-discovery
WORKFLOW = Workflow(
    "planner-lite",
    StepDef(id="context_capture", title="Context Capture and Exploration", actions=STEPS[1]["actions"]),
    StepDef(id="approach_generation", title="Approach Generation and Decisions", actions=STEPS[2]["actions"]),
    StepDef(id="milestone_definition", title="Milestone Definition and Plan Writing", actions=STEPS[3]["actions"]),
    StepDef(id="self_review", title="Self-Review", actions=[]),  # Dynamic actions
    description="Lightweight planning without subagent dispatch",
    validate=False,
)


def main():
    """Entry point for planner-lite planning workflow."""
    parser = argparse.ArgumentParser(
        description="Planner-lite - Lightweight planning without subagent dispatch",
        epilog="Steps: 1-4 (Context -> Approach -> Milestones -> Review)",
    )
    parser.add_argument("--step", type=int, required=True, help="Step number (1-4)")
    parser.add_argument(
        "--state-dir",
        type=str,
        help="State directory (created in step 1, required for steps 2-4)",
    )
    parser.add_argument(
        "--iteration",
        type=int,
        default=1,
        help="Current iteration for step 4 self-review (1-3)",
    )
    args = parser.parse_args()

    # Validate step number
    if args.step < 1 or args.step > 4:
        sys.exit(f"ERROR: Invalid step {args.step}. Must be 1-4.")

    # Validate state_dir for steps 2+
    if args.step >= 2 and not args.state_dir:
        sys.exit(f"ERROR: --state-dir required for step {args.step}")

    step_info = STEPS.get(args.step)
    if not step_info:
        sys.exit(f"ERROR: Invalid step {args.step}")

    handler = STEP_HANDLERS.get(args.step)
    if not handler:
        sys.exit(f"ERROR: No handler for step {args.step}")

    output = handler(args, step_info)
    print(output)


if __name__ == "__main__":
    main()
