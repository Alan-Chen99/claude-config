#!/usr/bin/env python3
"""Regenerate system prompt snapshots by running capture.py for each variant.

Output: <model>/<variant>/{request.json, system-prompt.md}

Usage:
    ./regenerate.py                      # all variants, default model (sonnet)
    ./regenerate.py default              # just one variant
    ./regenerate.py custom-output-style  # just one (prefix match)
    ./regenerate.py --model haiku        # different model
    ./regenerate.py --list               # show available variants
"""

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
CAPTURE = SCRIPT_DIR / "capture.py"

CUSTOM_PROMPT = "You are a custom assistant."

# Each variant: (claude_args, capture_flags)
# claude_args: flags passed to claude CLI
# capture_flags: flags consumed by capture.py (--capture-output-style, etc.)
VARIANTS: dict[str, dict] = {
    # --- output style variants (no CLI flags) ---
    "default": {
        "claude_args": [],
        "capture_flags": ["--capture-output-style", "default"],
    },
    "custom-output-style": {
        "claude_args": [],
        "capture_flags": ["--capture-output-style", "Explanatory"],
    },
    # --- CLI flag variants ---
    "system-prompt": {
        "claude_args": ["--system-prompt", CUSTOM_PROMPT],
        "capture_flags": ["--capture-output-style", "default"],
    },
    "system-prompt-file": {
        "claude_args": None,  # temp file, handled specially
        "capture_flags": ["--capture-output-style", "default"],
    },
    "append": {
        "claude_args": ["--append-system-prompt", CUSTOM_PROMPT],
        "capture_flags": ["--capture-output-style", "default"],
    },
}


def run_variant(name: str, variant: dict, model: str) -> bool:
    out_dir = SCRIPT_DIR / model / name
    print(f"\n{'='*60}")
    print(f"  {model}/{name}/")
    print(f"{'='*60}")

    claude_args = variant["claude_args"]
    capture_flags = variant.get("capture_flags", [])
    tmp_prompt_file = None

    if claude_args is None:
        tmp_prompt_file = tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", prefix="prompt-", delete=False
        )
        tmp_prompt_file.write(CUSTOM_PROMPT)
        tmp_prompt_file.close()
        claude_args = ["--system-prompt-file", tmp_prompt_file.name]

    try:
        result = subprocess.run(
            [
                sys.executable, str(CAPTURE),
                "--capture-model", model,
                *capture_flags,
                *claude_args,
            ],
            cwd=SCRIPT_DIR,
            capture_output=True,
            text=True,
            timeout=60,
        )
    except subprocess.TimeoutExpired:
        print(f"  TIMEOUT", file=sys.stderr)
        return False
    finally:
        if tmp_prompt_file:
            Path(tmp_prompt_file.name).unlink(missing_ok=True)

    if result.returncode != 0:
        print(f"  FAILED (exit {result.returncode})", file=sys.stderr)
        if result.stderr:
            print(f"  {result.stderr.strip()}", file=sys.stderr)
        return False

    cap_dir = SCRIPT_DIR / "capture-output"
    system_src = cap_dir / "system.txt"
    request_src = cap_dir / "request.json"

    if not system_src.exists() or not request_src.exists():
        print(f"  FAILED: capture-output missing", file=sys.stderr)
        return False

    out_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(request_src, out_dir / "request.json")
    shutil.copy2(system_src, out_dir / "system-prompt.md")

    req_size = (out_dir / "request.json").stat().st_size
    sys_size = (out_dir / "system-prompt.md").stat().st_size
    print(f"  request.json      ({req_size:,} chars)")
    print(f"  system-prompt.md  ({sys_size:,} chars)")

    if result.stderr:
        for line in result.stderr.strip().splitlines():
            print(f"  {line}")

    return True


def resolve_name(arg: str) -> str:
    if arg in VARIANTS:
        return arg
    matches = [k for k in VARIANTS if k.startswith(arg)]
    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        print(f"Ambiguous prefix '{arg}': {matches}", file=sys.stderr)
        sys.exit(1)
    print(f"Unknown variant '{arg}'. Available: {list(VARIANTS.keys())}", file=sys.stderr)
    sys.exit(1)


def main() -> None:
    argv = sys.argv[1:]

    if "--list" in argv or "-l" in argv:
        for name in VARIANTS:
            print(f"  {name}")
        return

    model = "sonnet"
    if "--model" in argv:
        idx = argv.index("--model")
        model = argv[idx + 1]
        argv = argv[:idx] + argv[idx + 2:]

    positional = [a for a in argv if not a.startswith("-")]
    targets = [resolve_name(a) for a in positional] if positional else list(VARIANTS)

    ok, fail = 0, 0
    for name in targets:
        if run_variant(name, VARIANTS[name], model):
            ok += 1
        else:
            fail += 1

    print(f"\nDone: {ok} ok, {fail} failed → {model}/")
    sys.exit(1 if fail else 0)


if __name__ == "__main__":
    main()
