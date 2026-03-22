#!/usr/bin/env python3
"""
Do - Meta-execution pipeline.

Six-step workflow:
  1. Reframe      - Transform request into actionable instruction
  2. Expectations  - Surface implicit user expectations
  3. Execute       - Execute the reframed instruction
  4. Followup      - Anticipate likely followups
  5. Gate          - Triage followup actions: skip, do now, or smoke-test
  6. Gate-Execute  - Execute gate-identified actions, then loop 6->4->5

Converts vague or passive requests into structured action with built-in
reflection and self-correction.
"""

import argparse
import sys
from pathlib import Path

from skills.lib.workflow.prompts import format_step

# ============================================================================
# CONFIGURATION
# ============================================================================

MODULE_PATH = "skills.do.do"
TOTAL_STEPS = 6

# skills/do/steps/ — prompt content lives in markdown, loaded at runtime
STEPS_DIR = Path(__file__).resolve().parent.parent.parent.parent / "do" / "steps"

STEP_TO_FILE: dict[int, tuple[str, str]] = {
    1: ("Reframe", "reframe.md"),
    2: ("Identify Expectations", "expectations.md"),
    3: ("Execute", "execute.md"),
    4: ("Anticipate Followup", "followup.md"),
    5: ("Gate", "gate.md"),
    6: ("Gate-Execute", "gate-execute.md"),
}


# ============================================================================
# STEP LOADING
# ============================================================================


def load_step(step: int) -> tuple[str, str]:
    """Load step title and instructions from markdown."""
    if step not in STEP_TO_FILE:
        sys.exit(f"ERROR: Unknown step {step}")

    title, filename = STEP_TO_FILE[step]
    path = STEPS_DIR / filename

    if not path.exists():
        sys.exit(f"ERROR: Step file not found: {path}")

    body = path.read_text().strip()
    return title, body


# ============================================================================
# MESSAGE BUILDERS
# ============================================================================


def build_next_command(step: int) -> str | None:
    """Build invoke command for next step."""
    base = f"python3 -m {MODULE_PATH}"
    if step == 1:
        return f"{base} --step 2"
    if step == 2:
        return f"{base} --step 3"
    if step == 3:
        return f"{base} --step 4"
    if step == 4:
        return f"{base} --step 5"
    if step == 6:
        return f"{base} --step 4"
    # Step 5 has inline routing in format_output (conditional on gate result)
    return None


# ============================================================================
# OUTPUT FORMATTING
# ============================================================================


def format_output(step: int) -> str:
    """Format output for the given step."""
    title, instructions = load_step(step)
    full_title = f"DO - {title}"

    # Step 5: conditional routing — format_step would add contradictory
    # WORKFLOW COMPLETE, so build output directly.
    if step == 5:
        execute_cmd = f"python3 -m {MODULE_PATH} --step 6"
        instructions += (
            f"\n\nIf no runnable actions: workflow complete, respond to user."
            f"\nIf any runnable actions: execute: {execute_cmd}"
        )
        header = f"{full_title}\n{'=' * len(full_title)}\n\n"
        return header + instructions

    next_cmd = build_next_command(step)
    return format_step(instructions, next_cmd or "", title=full_title)


# ============================================================================
# ENTRY POINT
# ============================================================================


def main():
    """Entry point for do workflow."""
    parser = argparse.ArgumentParser(
        description="Do - Meta-execution pipeline",
        epilog="Steps: reframe (1) -> expectations (2) -> execute (3) -> followup (4) -> gate (5) -> gate-execute (6) -> loop 4-5-6",
    )
    parser.add_argument("--step", type=int, required=True)

    args = parser.parse_args()

    if args.step < 1 or args.step > TOTAL_STEPS:
        sys.exit(f"ERROR: --step must be 1-{TOTAL_STEPS}")

    print(format_output(args.step))


if __name__ == "__main__":
    main()
