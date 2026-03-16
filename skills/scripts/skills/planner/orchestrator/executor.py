#!/usr/bin/env python3
"""
Plan Executor - Execute approved plans through delegation.

Nine-step workflow:
  1. Execution Planning - analyze plan, build wave list
  2. Reconciliation - validate existing code (conditional)
  3. Implementation - dispatch developers (wave-aware parallel)
  4. Code QR - verify code quality (RULE 0/1/2)
  5. Code QR Gate - route pass/fail
  6. Documentation - TW pass
  7. Doc QR - verify documentation quality
  8. Doc QR Gate - route pass/fail
  9. Retrospective - present summary
"""

import argparse
import sys

from skills.lib.workflow.types import AgentRole
from skills.lib.workflow.prompts import subagent_dispatch
from skills.lib.workflow.prompts.step import format_step
from skills.planner.shared.qr.cli import add_qr_args
from skills.planner.shared.qr.types import QRState, QRStatus, GateConfig, LoopState
from skills.planner.shared.resources import get_mode_script_path
from skills.planner.shared.builders import (
    THINKING_EFFICIENCY,
    format_forbidden,
    format_gate_result,
    PEDANTIC_ENFORCEMENT,
)
from skills.planner.shared.constraints import (
    ORCHESTRATOR_CONSTRAINT,
    format_state_banner,
)


# Module path for -m invocation
MODULE_PATH = "skills.planner.orchestrator.executor"


# =============================================================================
# Direct dispatch prompts (no script invocation)
# Used when sub-agent receives task via prompt rather than mode script.
# =============================================================================

IMPL_CODE_QR_PROMPT = """\
Review all implemented code against the plan's acceptance criteria.

For EACH milestone in the plan:
  1. Read the acceptance criteria
  2. Read the implemented code files
  3. Verify each criterion is satisfied

Also check:
  - Cross-cutting concerns (error handling, logging, shared state)
  - Code quality (structure, patterns, no god objects/functions)
  - Intent marker validation
  - Implementation drift from plan

OUT OF SCOPE: Plan structure, documentation files.

Report format:
  PASS - if all criteria met and code quality verified
  ISSUES - with findings grouped by milestone"""

IMPL_DOCS_QR_PROMPT = """\
Review all post-implementation documentation against plan requirements.

Check:
  - CLAUDE.md files: tabular index format, presence in modified directories
  - README.md: creation criteria, accuracy
  - Code comments: explain WHY not WHAT, no temporal contamination
  - Invisible knowledge transfer: docs adjacent to code

OUT OF SCOPE: Code quality, plan structure.

Report format:
  PASS - if documentation meets all requirements
  ISSUES - with specific findings and locations"""

CODE_FIX_PROMPT = """\
Code QR found issues in implemented code. Apply targeted fixes.

1. Read the Code QR report findings from the orchestrator's context
2. For EACH failed item:
   - Understand the issue from the finding description
   - Locate the relevant code
   - Apply a targeted fix (minimal change to resolve the issue)
3. Run tests to validate fixes: pytest / tsc / go test -race
   Pass criteria: 100% tests pass, zero warnings"""


def direct_dispatch(agent_type: str, task_prompt: str) -> str:
    """Generate dispatch block with direct task prompt (no script invocation).

    Use when the sub-agent should follow prompt instructions directly,
    rather than invoking a mode script as its first action.
    """
    return (
        "DISPATCH SUB-AGENT\n"
        "==================\n"
        "\n"
        f"ACTION: Use the Task tool to spawn a {agent_type} agent.\n"
        "\n"
        "Task tool parameters:\n"
        f"  - subagent_type: {agent_type}\n"
        "  - prompt: Include the full task description below\n"
        "  - run_in_background: NEVER set this. Always omit or set false.\n"
        "\n"
        "TASK FOR THE SUB-AGENT:\n"
        f"{task_prompt}\n"
        "\n"
        "After the sub-agent returns, continue with the next workflow step."
    )


def detect_reconciliation_signals(user_request: str) -> bool:
    """Detect if user request requires reconciliation phase."""
    signals = ["already implemented", "resume", "partially complete",
               "existing code", "continue from"]
    return any(s in user_request.lower() for s in signals)


STEPS = {
    1: {
        "title": "Execution Planning",
        "actions": [
            "Plan file: $PLAN_FILE (substitute from context)",
            "",
            "ANALYZE plan:",
            "  - Count milestones and parse dependency diagram",
            "  - Group milestones into WAVES for execution",
            "  - Set up TodoWrite tracking",
            "",
            "WAVE ANALYSIS:",
            "  Parse the plan's 'Milestone Dependencies' diagram.",
            "  Group into waves: milestones at same depth = one wave.",
            "",
            "  Example diagram:",
            "    M0 (foundation)",
            "     |",
            "     +---> M1 (auth)     \\",
            "     |                    } Wave 2 (parallel)",
            "     +---> M2 (users)    /",
            "     |",
            "     +---> M3 (posts) ----> M4 (feed)",
            "            Wave 3          Wave 4",
            "",
            "  Output format:",
            "    Wave 1: [0]       (foundation, sequential)",
            "    Wave 2: [1, 2]    (parallel)",
            "    Wave 3: [3]       (sequential)",
            "    Wave 4: [4]       (sequential)",
            "",
            "WORKFLOW:",
            "  This step is ANALYSIS ONLY. Do NOT delegate yet. PROHIBITED: read files other than $PLAN_FILE",
            "  Record wave groupings for step 3 (Implementation).",
        ],
    },
    2: {
        "title": "Reconciliation",
        "is_dispatch": True,
        "dispatch_agent": "quality-reviewer",
        "mode_script": "quality_reviewer/exec-reconcile.py",
        "invoke_suffix": " --milestone N",
        "pre_dispatch": [
            "Validate existing code against plan requirements BEFORE executing.",
            "",
            "For EACH milestone, launch quality-reviewer agent:",
        ],
        "post_dispatch": [
            "The sub-agent will invoke the script and follow its guidance.",
            "",
            "Expected output: SATISFIED | NOT_SATISFIED | PARTIALLY_SATISFIED",
        ],
        "routing": {
            "SATISFIED": "Mark milestone complete, skip execution",
            "NOT_SATISFIED": "Execute milestone normally",
            "PARTIALLY_SATISFIED": "Execute only missing parts",
        },
        "extra_instructions": [
            "",
            "Parallel execution: May run reconciliation for multiple milestones",
            "in parallel (multiple Task calls in single response) when milestones",
            "are independent.",
        ],
    },
    3: {
        "title": "Implementation",
    },
    4: {
        "title": "Code QR",
        "is_qr": True,
        "qr_name": "CODE QR",
        "is_dispatch": True,
        "dispatch_agent": "quality-reviewer",
        "pre_dispatch": [
            "<qa_integration>",
            "Before QR code review, run post-implementation QA.",
            "",
            "1. DISPATCH QA decomposition:",
            "   python3 -m skills.planner.qa.decompose --step 1",
            "   Context: PLAN_FILE, MODIFIED_FILES, STATE_DIR (if available)",
            "   Phase: post-implementation",
            "",
            "2. Once decomposition complete, read qa.yaml from STATE_DIR.",
            "",
            "3. For each item where scope != '*': dispatch parallel verifier.",
            "   For each item where scope == '*': dispatch sequential verifier.",
            "",
            "4. Aggregate results into qa.yaml (update status/finding fields).",
            "",
            "5. Then proceed with Code QR review below.",
            "</qa_integration>",
            "",
        ],
        "post_dispatch": [
            "The sub-agent will invoke the script and follow its guidance.",
            "",
            "Expected output: PASS or ISSUES (XML grouped by milestone).",
        ],
        "post_qr_routing": {"self_fix": False, "fix_target": "developer"},
    },
    # Step 5 is the Code QR gate - handled separately
    6: {
        "title": "Documentation",
    },
    7: {
        "title": "Doc QR",
        "is_qr": True,
        "qr_name": "DOC QR",
        "is_dispatch": True,
        "dispatch_agent": "quality-reviewer",
        "post_dispatch": [
            "The sub-agent will invoke the script and follow its guidance.",
            "",
            "Expected output: PASS or ISSUES.",
        ],
        "post_qr_routing": {"self_fix": False, "fix_target": "technical-writer"},
    },
    # Step 8 is the Doc QR gate - handled separately
    9: {
        "title": "Retrospective",
        "actions": [
            "PRESENT retrospective to user (do not write to file):",
            "",
            "EXECUTION RETROSPECTIVE",
            "=======================",
            "Plan: [path]",
            "Status: COMPLETED | BLOCKED | ABORTED",
            "",
            "Milestone Outcomes: | Milestone | Status | Notes |",
            "Reconciliation Summary: [if run]",
            "Plan Accuracy Issues: [if any]",
            "Deviations from Plan: [if any]",
            "Quality Review Summary: [counts by category]",
            "Feedback for Future Plans: [actionable suggestions]",
        ],
    },
}


# Gate configuration for step 5 (Code QR Gate)
CODE_QR_GATE = GateConfig(
    qr_name="Code QR",
    work_step=3,
    pass_step=6,
    pass_message="Code quality verified. Proceed to documentation.",
    fix_target=AgentRole.DEVELOPER,
)

# Gate configuration for step 8 (Doc QR Gate)
DOC_QR_GATE = GateConfig(
    qr_name="Doc QR",
    work_step=6,
    pass_step=9,
    pass_message="Documentation verified. Proceed to retrospective.",
    fix_target=AgentRole.TECHNICAL_WRITER,
)


def format_gate(step: int, gate: GateConfig, qr: QRState, total_steps: int) -> str:
    """Format gate step output."""
    parts = []

    # Gate result banner
    parts.append(format_gate_result(qr.passed))
    parts.append("")

    if qr.passed:
        parts.append(gate.pass_message)
        parts.append("")
        parts.append(format_forbidden(
            "Asking the user whether to proceed - the workflow is deterministic",
            "Offering alternatives to the next step - all steps are mandatory",
            "Interpreting 'proceed' as optional - EXECUTE immediately",
        ))
    else:
        parts.append(PEDANTIC_ENFORCEMENT)
        parts.append("")

        fix_target = gate.fix_target.value if gate.fix_target else "developer"
        parts.append("NEXT ACTION:")
        parts.append("  Invoke the next step command.")
        parts.append(f"  The next step will dispatch {fix_target} with fix guidance.")
        parts.append("")

        parts.append(format_forbidden(
            "Fixing issues directly from this gate step",
            "Spawning agents directly from this gate step",
            "Using Edit/Write tools yourself",
            "Proceeding without invoking the next step",
            "Interpreting 'minor issues' as skippable",
            "Claiming 'diminishing returns' or 'comprehensive enough'",
            "Proceeding to next phase without QR PASS",
        ))

    body = "\n".join(parts)

    # Determine next command
    if qr.passed and gate.pass_step is not None:
        next_cmd = f"python3 -m {MODULE_PATH} --step {gate.pass_step}"
    else:
        next_iteration = qr.iteration + 1
        next_cmd = f"python3 -m {MODULE_PATH} --step {gate.work_step} --qr-fail --qr-iteration {next_iteration}"

    return format_step(body, next_cmd, title=f"{gate.qr_name} Gate")


def format_step_3_implementation(qr: QRState, total_steps: int, milestone_count: int) -> str:
    """Format step 3 implementation output."""
    if qr.state == LoopState.RETRY:
        title = "Implementation - Fix Mode"
    else:
        title = "Implementation"

    actions = []
    if qr.state == LoopState.RETRY:
        actions.append(format_state_banner("IMPLEMENTATION FIX", qr.iteration, "fix"))
        actions.append("")
        actions.append("FIX MODE: Code QR found issues.")
        actions.append("")
        actions.append(ORCHESTRATOR_CONSTRAINT)
        actions.append("")

        actions.append(direct_dispatch(
            agent_type="developer",
            task_prompt=CODE_FIX_PROMPT,
        ))
        actions.append("")
        actions.append("Developer reads QR report and fixes issues in <milestone> blocks.")
        actions.append("After developer completes, re-run Code QR for fresh verification.")
    else:
        actions.extend([
            "Execute ALL milestones using wave-aware parallel dispatch.",
            "",
            "WAVE-AWARE EXECUTION:",
            "  - Milestones within same wave: dispatch in PARALLEL",
            "    (Multiple Task calls in single response)",
            "  - Waves execute SEQUENTIALLY",
            "    (Wait for wave N to complete before starting wave N+1)",
            "",
            "Use waves identified in step 1.",
            "",
            ORCHESTRATOR_CONSTRAINT,
            "",
            "FOR EACH WAVE:",
            "  1. Dispatch a developer agent for EACH milestone in wave:",
            "     Task(developer): Milestone N",
            "",
            "  2. Each prompt must use exactly this template:",
            "     > Execute Milestone $N of $PLAN_FILE.",
            "     > Pass criteria:",
            "     > - [ ] Run tests: pytest / tsc / go test -race; 100% tests pass, zero warnings",
            "     > - [ ] Acceptance criteria of Milestone $N in $PLAN_FILE met.",
            "     > - [ ] Tests of Milestone $N in $PLAN_FILE passes.",
            "",
            "     Do NOT substitue acceptance criteria from $PLAN_FILE",
            "     Do NOT repeat content already in any file; point to the file instead.",
            "",
            "  3. Wait for ALL agents in wave to complete",
            "",
            "  4. For each agent output, assess:",
            "       (a) ACCEPTANCE CRITERIA: Were acceptance criteria met?",
            "       (b) COMPLETENESS: Plan partially executed? Only ran a subset of tests?",
            "       (c) CLAIMS: Verify any claims that may not be properly verified.",
            "       (d) DEVIATIONS: If deviation from the plan: is this the right approach? alternatives?",
            "",
            "     RATING SCALE:",
            "       - PASS: Proceed",
            "       - FAIL: Use another developer or debugger to fix,",
            "",
            "  5. Proceed to next wave (repeat 1-4)",
            "",
            "After ALL waves complete, proceed to Code QR.",
            "",
            "ERROR HANDLING (you NEVER fix code yourself):",
            "  Clear problem + solution: Task(developer) immediately",
            "  Difficult/unclear problem: Task(debugger) to diagnose first",
            "  Uncertain how to proceed: AskUserQuestion with options",
        ])

    body = "\n".join(actions)
    next_cmd = f"python3 -m {MODULE_PATH} --step 4"

    return format_step(body, next_cmd, title=title)


def format_step_6_documentation(qr: QRState, total_steps: int) -> str:
    """Format step 6 documentation output."""
    mode_script = get_mode_script_path("technical_writer/exec-docs.py")

    if qr.state == LoopState.RETRY:
        title = "Documentation - Fix Mode"
    else:
        title = "Documentation"

    actions = []

    if qr.state == LoopState.RETRY:
        actions.append(format_state_banner("DOCUMENTATION FIX", qr.iteration, "fix"))
        actions.append("")
        actions.append("FIX MODE: Doc QR found issues.")
        actions.append("")
        actions.append(ORCHESTRATOR_CONSTRAINT)
        actions.append("")

        invoke_cmd = f"python3 -m {mode_script} --step 1 --qr-fail --qr-iteration {qr.iteration}"
        actions.append(subagent_dispatch(
            agent_type="technical-writer",
            command=invoke_cmd,
        ))
    else:
        actions.append(ORCHESTRATOR_CONSTRAINT)
        actions.append("")

        invoke_cmd = f"python3 -m {mode_script} --step 1"
        actions.append(subagent_dispatch(
            agent_type="technical-writer",
            command=invoke_cmd,
        ))

    body = "\n".join(actions)
    next_cmd = f"python3 -m {MODULE_PATH} --step 7"

    return format_step(body, next_cmd, title=title)


def format_step_1_planning(qr: QRState, total_steps: int, reconciliation_check: bool, **kw) -> str:
    """Format step 1 planning output."""
    info = STEPS[1]

    actions = list(info["actions"])
    # actions.extend([
    #     "",
    #     "=" * 70,
    #     "MANDATORY NEXT ACTION",
    #     "=" * 70,
    # ])
    if reconciliation_check:
        next_cmd = f"python3 -m {MODULE_PATH} --step 2 --reconciliation-check"
    else:
        actions.extend([
            # "Proceed to Implementation step.",
            # "Proceed to Implementation step.",
            # "Use the wave groupings from your analysis.",
            # "=" * 70,
        ])
        next_cmd = f"python3 -m {MODULE_PATH} --step 3"

    body_parts = []
    body_parts.append(THINKING_EFFICIENCY)
    body_parts.append("")
    body_parts.extend(actions)

    body = "\n".join(body_parts)
    return format_step(body, next_cmd, title=info["title"])


def format_step_4_code_qr(qr: QRState, total_steps: int, **kw) -> str:
    """Format step 4 code QR output with branching."""
    info = STEPS[4]

    actions = []
    actions.append(format_state_banner(info["qr_name"], qr.iteration, "fresh_review"))
    actions.append("")

    pre_dispatch = info.get("pre_dispatch", [])
    actions.extend(pre_dispatch)

    actions.append(ORCHESTRATOR_CONSTRAINT)
    actions.append("")

    actions.append(direct_dispatch(
        agent_type=info.get("dispatch_agent", "quality-reviewer"),
        task_prompt=IMPL_CODE_QR_PROMPT,
    ))
    actions.append("")

    post_dispatch = info.get("post_dispatch", [])
    actions.extend(post_dispatch)

    body = "\n".join(actions)
    if_pass = f"python3 -m {MODULE_PATH} --step 5 --qr-status pass"
    if_fail = f"python3 -m {MODULE_PATH} --step 5 --qr-status fail"

    return format_step(body, title=info["title"], if_pass=if_pass, if_fail=if_fail)


def format_step_7_doc_qr(qr: QRState, total_steps: int, **kw) -> str:
    """Format step 7 doc QR output with branching."""
    info = STEPS[7]

    actions = []
    actions.append(format_state_banner(info["qr_name"], qr.iteration, "fresh_review"))
    actions.append("")

    pre_dispatch = info.get("pre_dispatch", [])
    actions.extend(pre_dispatch)

    actions.append(ORCHESTRATOR_CONSTRAINT)
    actions.append("")

    actions.append(direct_dispatch(
        agent_type=info.get("dispatch_agent", "quality-reviewer"),
        task_prompt=IMPL_DOCS_QR_PROMPT,
    ))
    actions.append("")

    post_dispatch = info.get("post_dispatch", [])
    actions.extend(post_dispatch)

    extra_instructions = info.get("extra_instructions", [])
    actions.extend(extra_instructions)

    body = "\n".join(actions)
    if_pass = f"python3 -m {MODULE_PATH} --step 8 --qr-status pass"
    if_fail = f"python3 -m {MODULE_PATH} --step 8 --qr-status fail"

    return format_step(body, title=info["title"], if_pass=if_pass, if_fail=if_fail)


STEP_HANDLERS = {
    1: format_step_1_planning,
    3: lambda qr, total_steps, milestone_count, **kw: format_step_3_implementation(qr, total_steps, milestone_count),
    4: format_step_4_code_qr,
    5: lambda qr, total_steps, qr_status, **kw: format_gate(5, CODE_QR_GATE, qr, total_steps) if qr_status else "Error: --qr-status required for step 5",
    6: lambda qr, total_steps, **kw: format_step_6_documentation(qr, total_steps),
    7: format_step_7_doc_qr,
    8: lambda qr, total_steps, qr_status, **kw: format_gate(8, DOC_QR_GATE, qr, total_steps) if qr_status else "Error: --qr-status required for step 8",
}


def format_output(step: int,
                  qr_iteration: int, qr_fail: bool, qr_status: str,
                  reconciliation_check: bool, milestone_count: int) -> str:
    """Format output for display."""
    from skills.planner.shared.constants import EXECUTOR_TOTAL_STEPS

    total_steps = EXECUTOR_TOTAL_STEPS

    # Construct QRState from legacy parameters
    status = QRStatus(qr_status) if qr_status else None
    state = LoopState.RETRY if qr_fail else LoopState.INITIAL
    qr = QRState(iteration=qr_iteration, state=state, status=status)

    # Dispatch to step-specific handlers
    handler = STEP_HANDLERS.get(step)
    if handler:
        return handler(qr=qr, total_steps=total_steps, qr_status=qr_status,
                      milestone_count=milestone_count, reconciliation_check=reconciliation_check)

    # Generic step handling
    info = STEPS.get(step, STEPS[9])

    # Handle QR step in fix mode (developer/TW fixes, not QR re-run)
    if info.get("is_qr") and qr.state == LoopState.RETRY:
        post_qr_config = info.get("post_qr_routing", {})
        fix_target = post_qr_config.get("fix_target", "developer")
        qr_name = info.get("qr_name", "QR")

        fix_actions = []
        fix_actions.append(format_state_banner(qr_name, qr.iteration, "fix"))
        fix_actions.append("")
        fix_actions.append(f"FIX MODE: {qr_name} found issues.")
        fix_actions.append("")
        fix_actions.append(ORCHESTRATOR_CONSTRAINT)
        fix_actions.append("")

        fix_prompt = (
            f"{qr_name} found issues. Apply targeted fixes.\n"
            "\n"
            "1. Read the QR report findings from the orchestrator's context\n"
            "2. For EACH failed item:\n"
            "   - Understand the issue\n"
            "   - Locate the relevant file\n"
            "   - Apply a targeted fix\n"
            "3. Validate fixes locally"
        )
        fix_actions.append(direct_dispatch(
            agent_type=fix_target,
            task_prompt=fix_prompt,
        ))

        body = "\n".join(fix_actions)
        next_cmd = f"python3 -m {MODULE_PATH} --step {step}"

        return format_step(body, next_cmd, title=f"{info['title']} - Fix Mode")

    is_complete = step >= total_steps

    # Build actions
    actions = []

    # Add QR banner for QR steps
    if info.get("is_qr"):
        qr_name = info.get("qr_name", "QR")
        actions.append(format_state_banner(qr_name, qr.iteration, "fresh_review"))
        actions.append("")

    # Handle dispatch steps
    if info.get("is_dispatch"):
        pre_dispatch = info.get("pre_dispatch", [])
        actions.extend(pre_dispatch)

        actions.append(ORCHESTRATOR_CONSTRAINT)
        actions.append("")

        mode_script = get_mode_script_path(info["mode_script"])
        dispatch_agent = info.get("dispatch_agent", "agent")
        invoke_suffix = info.get("invoke_suffix", "")
        invoke_cmd = f"python3 -m {mode_script} --step 1{invoke_suffix}"

        actions.append(subagent_dispatch(
            agent_type=dispatch_agent,
            command=invoke_cmd,
        ))
        actions.append("")

        post_dispatch = info.get("post_dispatch", [])
        actions.extend(post_dispatch)
    elif "actions" in info:
        actions.extend(info["actions"])

    # Build next command
    if is_complete:
        actions.append("")
        actions.append("EXECUTION COMPLETE - Present retrospective to user.")
        next_cmd = ""
    else:
        next_cmd = f"python3 -m {MODULE_PATH} --step {step + 1}"

    body = "\n".join(actions)
    return format_step(body, next_cmd, title=info["title"])


def main():
    parser = argparse.ArgumentParser(
        description="Plan Executor - Execute approved plans",
        epilog="Steps: plan -> reconcile -> implement -> code QR -> gate -> docs -> doc QR -> gate -> retrospective",
    )

    parser.add_argument("--step", type=int, required=True)
    add_qr_args(parser)
    parser.add_argument("--qr-iteration", type=int, default=0)
    parser.add_argument("--qr-fail", action="store_true")
    parser.add_argument("--reconciliation-check", action="store_true")
    parser.add_argument("--milestone-count", type=int, default=0)

    args = parser.parse_args()

    if args.step < 1 or args.step > 9:
        sys.exit("Error: step must be 1-9")

    if args.step == 5 and not args.qr_status:
        sys.exit("Error: --qr-status required for step 5")

    if args.step == 8 and not args.qr_status:
        sys.exit("Error: --qr-status required for step 8")

    print(format_output(args.step,
                        args.qr_iteration, args.qr_fail, args.qr_status,
                        args.reconciliation_check, args.milestone_count))


if __name__ == "__main__":
    main()
