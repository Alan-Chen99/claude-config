#!/usr/bin/env python3
"""
Prompt Patch - Structured prompt change workflow.

Eleven-step workflow:
  1.  Motivation        - Why change? What breaks if we don't?
  2.  Brainstorm        - Rapid unfiltered idea generation (10+ one-liners)
  3.  Identify          - Target state + workflow options from brainstorm
  4.  Draft Options     - Prompt updates per option
  5.  Context Check     - System prompt/instructions alignment; failure points
  6.  Regressions       - Identify regressions; revise
  7.  Pick & Draft      - Select best option; full draft
  8.  Deterministic     - Crash/silent-fail/impossible-to-follow checks
  9.  Non-deterministic - Agent mistake modes
  10. Top Concerns      - 3 problems not covered above
  11. Final             - Write final version

All steps live in a single steps.md file, separated by `<!--step N: name-->`
markers. This script parses the file and prints the requested step.
"""

import argparse
import re
import sys
from pathlib import Path

# ============================================================================
# CONFIGURATION
# ============================================================================

TOTAL_STEPS = 11

STEPS_FILE = Path(__file__).resolve().parent.parent.parent.parent / "prompt-patch" / "steps.md"

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
    """Entry point for prompt-patch workflow."""
    parser = argparse.ArgumentParser(
        description="Prompt Patch - Structured prompt change workflow",
        epilog="Steps: motivation (1) -> brainstorm (2) -> identify (3) -> draft-options (4) -> context-check (5) -> regressions (6) -> pick-draft (7) -> deterministic (8) -> non-deterministic (9) -> concerns (10) -> final (11)",
    )
    parser.add_argument("--step", type=int, required=True)

    args, _extra = parser.parse_known_args()

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
