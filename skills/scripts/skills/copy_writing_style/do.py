#!/usr/bin/env python3
"""
Copy Writing Style - Generic style-matched content generation.

Three-phase workflow with iteration:
  1. Extract   - Read reference, identify ranked distinguishing features
  2. Draft     - Write or rewrite content targeting top features
  3. Iterate   - Self-critique and revise (loops until convergence or max rounds)

Steps live in steps.md, separated by `<!-- step N: name -->` markers.
Style reference injected at steps 1 and 3 via {STYLE_REF_CONTENT} placeholder.
Iteration count injected at step 3 via {ITERATION} and {NEXT_ITERATION} placeholders.

State: style-ref path is persisted to /tmp at step 1 and read back at step 3,
so the agent only needs to pass --style-ref once.
"""

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

TOTAL_STEPS = 3
MAX_ITERATIONS = 3

STEPS_FILE = Path(__file__).resolve().parent.parent.parent.parent / "copy-writing-style" / "steps.md"

SEPARATOR = re.compile(r"^<!--\s*step\s+(\d+):\s*(.+?)\s*-->$", re.MULTILINE)

STYLE_REF_PLACEHOLDER = "{STYLE_REF_CONTENT}"
ITERATION_PLACEHOLDER = "{ITERATION}"
NEXT_ITERATION_PLACEHOLDER = "{NEXT_ITERATION}"

STATE_DIR = Path("/tmp")


def state_file_path(style_ref: str) -> Path:
    """Compute state file path from style-ref path."""
    h = hashlib.sha256(style_ref.encode()).hexdigest()[:12]
    return STATE_DIR / f"copy-style-{h}.json"


def save_state(style_ref: str) -> None:
    """Persist style-ref path for subsequent steps."""
    # Use a well-known name so step 3 can find it without knowing the hash
    path = STATE_DIR / "copy-style-latest.json"
    path.write_text(json.dumps({"style_ref": style_ref}))


def load_state() -> str:
    """Load persisted style-ref path."""
    path = STATE_DIR / "copy-style-latest.json"
    if not path.exists():
        sys.exit("ERROR: No state file found. Run step 1 with --style-ref first.")
    data = json.loads(path.read_text())
    return data["style_ref"]


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


def load_style_ref(path: str) -> str:
    """Read style reference file content."""
    ref_path = Path(path).expanduser().resolve()
    if not ref_path.exists():
        sys.exit(f"ERROR: Style reference file not found: {ref_path}")
    return ref_path.read_text()


def main():
    """Entry point for copy-writing-style workflow."""
    parser = argparse.ArgumentParser(
        description="Copy Writing Style - style-matched content generation",
    )
    parser.add_argument("--step", type=int, required=True)
    parser.add_argument("--style-ref", type=str, default="")
    parser.add_argument("--iteration", type=int, default=0)

    args, _extra = parser.parse_known_args()

    if args.step < 1 or args.step > TOTAL_STEPS:
        sys.exit(f"ERROR: --step must be 1-{TOTAL_STEPS}")

    if not STEPS_FILE.exists():
        sys.exit(f"ERROR: Steps file not found: {STEPS_FILE}")

    steps = parse_steps(STEPS_FILE.read_text())

    if args.step not in steps:
        sys.exit(f"ERROR: Step {args.step} not found in {STEPS_FILE}")

    # At step 1, persist the style-ref path
    if args.step == 1:
        if not args.style_ref:
            sys.exit("ERROR: --style-ref is required at step 1")
        save_state(str(Path(args.style_ref).expanduser().resolve()))

    # Check iteration cap at step 3
    if args.step == 3 and args.iteration >= MAX_ITERATIONS:
        print(
            f"Maximum iterations ({MAX_ITERATIONS}) reached. "
            "Deliver your current draft as final."
        )
        return

    output = steps[args.step]

    # Inject style reference content at steps that need it
    if STYLE_REF_PLACEHOLDER in output:
        # Use provided --style-ref if given, otherwise load from state
        style_ref_path = args.style_ref if args.style_ref else load_state()
        ref_content = load_style_ref(style_ref_path)
        output = output.replace(STYLE_REF_PLACEHOLDER, ref_content)

    # Inject iteration count at step 3
    if ITERATION_PLACEHOLDER in output:
        output = output.replace(ITERATION_PLACEHOLDER, str(args.iteration))
    if NEXT_ITERATION_PLACEHOLDER in output:
        output = output.replace(NEXT_ITERATION_PLACEHOLDER, str(args.iteration + 1))

    print(output)


if __name__ == "__main__":
    main()
