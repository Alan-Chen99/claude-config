#!/usr/bin/env python3
"""
Do - Meta-execution pipeline.

Seven-step workflow:
  1. Reframe       - Transform request into actionable instruction
  2. Expectations  - Surface implicit user expectations
  3. Execute       - Execute the reframed instruction
  4. Followup      - Anticipate likely followups
  5. Gate          - Triage followup actions, then ROUTE: iterate (step 6) or terminate (step 7)
  6. Gate-Execute  - Execute gate-identified actions, then loop back to step 4 with --iteration=N+1
  7. Done          - Closure summary against step-2 expectations; terminal step

Loop 4-5-6 carries an --iteration=N arg the agent passes through; step 6
increments N when re-invoking step 4. The arg is captured-and-discarded by
parse_known_args — it exists for observability in tool-call logs, not for
script control flow.

All steps live in a single steps.md file, separated by `<!-- step N: name -->`
markers. This script parses the file and prints the requested step.
"""

import argparse
import re
import sys
from pathlib import Path

# ============================================================================
# CONFIGURATION
# ============================================================================

TOTAL_STEPS = 7

# skills/do/steps.md — all steps in one file, separated by <!-- step N: name -->
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
        epilog="Steps: reframe (1) -> expectations (2) -> execute (3) -> followup (4) -> gate (5) -> {gate-execute (6) -> loop 4-5-6 with --iteration=N+1, OR done (7)}",
    )
    parser.add_argument("--step", type=int, required=True)

    # Extra args capture step output from the model. Accepted and
    # discarded — the value is in making the model externalize state into
    # the tool call (same technique as pre_output.record).
    #
    # --iteration=N is one such arg: passed through steps 4/5/6 and into
    # step 7 on terminate. Observability-only. Do not promote it to a
    # required arg or use it for control flow without auditing every
    # invocation site in skills/do/steps.md.
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
