#!/usr/bin/env python3
"""Capture the system prompt from a Claude Code interactive session.

Uses expect to spawn claude with a real pty (true interactive mode). This
matters because the system prompt differs between interactive and -p mode
(identity block, gitStatus appending).

Usage:
    ./capture.py                                        # default prompt
    ./capture.py --system-prompt "custom prompt"        # with --system-prompt
    ./capture.py --system-prompt-file /path/to/file     # with --system-prompt-file
    ./capture.py --append-system-prompt "extra"         # with --append-system-prompt

Output:
    stdout: system prompt text (blocks joined by ---BLOCK_SEPARATOR---)
    capture-output/system.txt     - same as stdout
    capture-output/request.json   - full API request (metadata redacted)
    capture-output/summary.json   - block structure and tool inventory
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
INTERCEPT = SCRIPT_DIR / "intercept.js"
OUT_DIR = SCRIPT_DIR / "capture-output"
HTTP_LOGS = Path.home() / ".claude" / "http-logs"

EXPECT_SCRIPT = """\
set timeout 25
# Prevent nested session detection
set env(CLAUDECODE) ""
unset env(CLAUDECODE)
spawn {*}$argv
sleep 4
send "say exactly: done\\r"
expect {
  timeout { send "/exit\\r" }
  -re {done} { send "/exit\\r" }
}
expect eof
"""


def get_log_dirs() -> set[str]:
    if not HTTP_LOGS.exists():
        return set()
    return {str(p) for p in HTTP_LOGS.iterdir() if p.is_dir()}


def find_main_request(new_dirs: list[Path]) -> Path | None:
    best, best_size = None, 0
    for d in new_dirs:
        for req_path in sorted(d.glob("*-request.json")):
            try:
                req = json.loads(req_path.read_text())
                size = sum(len(s.get("text", "")) for s in req.get("system", []))
                if size > best_size:
                    best_size = size
                    best = req_path
            except (json.JSONDecodeError, OSError):
                continue
    return best


def spawn_claude(extra_args: list[str]) -> None:
    exp_file = tempfile.NamedTemporaryFile(
        mode="w", suffix=".exp", prefix="capture-", delete=False
    )
    exp_file.write(EXPECT_SCRIPT)
    exp_file.close()

    env = os.environ.copy()
    env["NODE_OPTIONS"] = f"--require {INTERCEPT}"

    try:
        subprocess.run(
            [
                "expect",
                "-f",
                exp_file.name,
                "--",
                "claude",
                "--model",
                "haiku",
                *extra_args,
            ],
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=35,
        )
    except subprocess.TimeoutExpired:
        pass
    finally:
        os.unlink(exp_file.name)


def extract(req_path: Path) -> None:
    req = json.loads(req_path.read_text())

    blocks = [s for s in req.get("system", []) if s.get("type") == "text"]
    texts = [s["text"] for s in blocks]
    content = "\n\n---BLOCK_SEPARATOR---\n\n".join(texts)

    if OUT_DIR.exists():
        shutil.rmtree(OUT_DIR)
    OUT_DIR.mkdir(parents=True)

    (OUT_DIR / "system.txt").write_text(content)

    if "metadata" in req:
        req["metadata"] = {k: "<redacted>" for k in req["metadata"]}
    (OUT_DIR / "request.json").write_text(json.dumps(req, indent=2))

    summary = {
        "version": next(
            (s["text"] for s in blocks if "cc_version" in s.get("text", "")), None
        ),
        "model": req.get("model"),
        "block_count": len(blocks),
        "total_chars": len(content),
        "blocks": [
            {"index": i, "length": len(s["text"]), "preview": s["text"][:200]}
            for i, s in enumerate(blocks)
        ],
        "tools": [t["name"] for t in req.get("tools", [])],
        "tool_description_chars": {
            t["name"]: len(t.get("description", "")) for t in req.get("tools", [])
        },
        "source_request": req_path.name,
    }
    (OUT_DIR / "summary.json").write_text(json.dumps(summary, indent=2))

    print(content)
    print(
        f"\n--- Captured {len(blocks)} blocks, {len(content)} chars "
        f"(model: {req.get('model')}) ---",
        file=sys.stderr,
    )


def main() -> None:
    extra_args = sys.argv[1:]

    before = get_log_dirs()
    spawn_claude(extra_args)
    after = get_log_dirs()

    new_dirs = [Path(d) for d in sorted(after - before)]
    if not new_dirs:
        print("ERROR: No API calls captured.", file=sys.stderr)
        sys.exit(1)

    req_path = find_main_request(new_dirs)
    if not req_path:
        print("ERROR: No system prompt found in captured requests.", file=sys.stderr)
        sys.exit(1)

    extract(req_path)


if __name__ == "__main__":
    main()
