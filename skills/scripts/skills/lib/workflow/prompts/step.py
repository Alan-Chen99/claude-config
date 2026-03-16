"""Step assembly for workflow prompts.

format_step() is the sole assembler. invoke_after logic is internal.
"""

from pathlib import Path

# SKILLS_DIR calculation matches subagent.py pattern: both modules are in
# skills/lib/workflow/prompts/, so .parent.parent.parent.parent.parent
# traverses: prompts/ -> workflow/ -> lib/ -> skills/ -> scripts/
SKILLS_DIR = Path(__file__).resolve().parent.parent.parent.parent.parent


def format_step(body: str, next_cmd: str = "", title: str = "",
                if_pass: str = "", if_fail: str = "") -> str:
    """Assemble complete workflow step: title + body + invoke directive.

    Args:
        body: Free-form prompt content (no wrapper needed)
        next_cmd: Command for next step (empty string signals completion)
        title: Optional title rendered as "TITLE\\n======\\n\\n" header
        if_pass: Branching command when QR gate passes
        if_fail: Branching command when QR gate fails

    Returns:
        Complete step output as plain text
    """
    if title:
        header = f"{title}\n{'=' * len(title)}\n\n"
        body = header + body

    if if_pass and if_fail:
        # Branching invoke for QR gate routing: the LLM chooses based on
        # aggregated QR outcome (all pass vs any fail).
        invoke = (
            f"NEXT STEP (MANDATORY -- execute exactly one):\n"
            f"    Working directory: {SKILLS_DIR}\n"
            f"    ALL agents returned PASS  ->  {if_pass}\n"
            f"    ANY agent returned FAIL   ->  {if_fail}\n\n"
            f"This is a mechanical routing decision. Do not interpret, summarize, "
            f"or assess the results.\n"
            f"Count PASS vs FAIL, then execute the matching command."
        )
        return f"{body}\n\n{invoke}"

    elif next_cmd:
        # Working directory is explicit because CLI execution context varies.
        # Command is literal shell invocation for next step.
        invoke = (
            f"NEXT STEP:\n"
            f"    Working directory: {SKILLS_DIR}\n"
            f"    Command: {next_cmd}\n\n"
            f"Execute this command now."
        )
        return f"{body}\n\n{invoke}"

    else:
        return f"{body}\n\nWORKFLOW COMPLETE (final step — no further steps exist) - Return the output from the step above. Do not summarize."


def format_step_error(message: str) -> str:
    """Emit structured error output — distinct from WORKFLOW COMPLETE.

    Used by mode_main when get_step_guidance returns an error dict
    or a dict missing the required 'actions' key.
    """
    return (
        f"WORKFLOW ERROR — HALTED\n"
        f"{'=' * 40}\n\n"
        f"{message}\n\n"
        f"DO NOT PROCEED. Do not use Edit, Write, or Bash tools on target files.\n"
        f"Return this error message to the orchestrator verbatim.\n\n"
        f"WORKFLOW ERROR — HALTED"
    )
