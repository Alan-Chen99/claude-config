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

All steps live in a single steps.md file, separated by `---step N: name---`
markers. This script parses the file and prints the requested step.
"""

import argparse
import re
import sys
from pathlib import Path

# ============================================================================
# CONFIGURATION
# ============================================================================

TOTAL_STEPS = 6

# skills/do/steps.md — all steps in one file, separated by ---step N: name---
STEPS_FILE = Path(__file__).resolve().parent.parent.parent.parent / "do" / "steps.md"

SEPARATOR = re.compile(r"^<!--\s*step\s+(\d+):\s*(.+?)\s*-->$", re.MULTILINE)


# ============================================================================
# PARSING
# ============================================================================


def parse_steps(text: str) -> dict[int, str]:
    """Split steps.md into {step_number: content} using separator markers."""
    markers = list(SEPARATOR.finditer(text))
    if not markers:
        sys.exit(f"ERROR: No step separators found in {STEPS_FILE}")

    steps: dict[int, str] = {}
    for i, match in enumerate(markers):
        step_num = int(match.group(1))
        start = match.end()
        end = markers[i + 1].start() if i + 1 < len(markers) else len(text)
        steps[step_num] = text[start:end].strip()

    return steps


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

    if not STEPS_FILE.exists():
        sys.exit(f"ERROR: Steps file not found: {STEPS_FILE}")

    steps = parse_steps(STEPS_FILE.read_text())

    if args.step not in steps:
        sys.exit(f"ERROR: Step {args.step} not found in {STEPS_FILE}")

    print(steps[args.step])


if __name__ == "__main__":
    main()
