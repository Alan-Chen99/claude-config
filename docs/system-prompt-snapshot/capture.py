#!/usr/bin/env python3
"""Capture system prompts from a Claude Code interactive session.

Uses expect to spawn claude with a real pty (true interactive mode). This
matters because the system prompt differs between interactive and -p mode
(identity block, gitStatus appending).

Usage:
    ./capture.py                                        # default prompt
    ./capture.py --system-prompt "custom prompt"        # with --system-prompt
    ./capture.py --system-prompt-file /path/to/file     # with --system-prompt-file
    ./capture.py --append-system-prompt "extra"         # with --append-system-prompt
    ./capture.py --subagent                             # also capture subagent prompts

Output:
    stdout: system prompt text (blocks joined by ---BLOCK_SEPARATOR---)
    capture-output/system.txt     - main system prompt (same as stdout)
    capture-output/request.json   - main API request (metadata redacted)
    capture-output/summary.json   - block structure and tool inventory
    capture-output/subagents/     - subagent prompts (when --subagent)
"""

import hashlib
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
# Accept trust dialog if it appears (new/unknown project dirs)
sleep 2
send "\\r"
# Use expect (not sleep) to drain pty output and prevent buffer-full blocking
set timeout 5
expect {
  timeout {}
  eof {}
}
send "say exactly: done\\r"
expect {
  timeout { send "/exit\\r" }
  -re {done} { send "/exit\\r" }
}
expect eof
"""

# Subagent mode: send a message that triggers an Agent tool call, then wait
# long enough for the subagent's API round-trip before exiting.
EXPECT_SCRIPT_SUBAGENT = """\
set timeout 120
set env(CLAUDECODE) ""
unset env(CLAUDECODE)
spawn {*}$argv
sleep 2
send "\\r"
# Use expect (not sleep) to consume pty output and prevent buffer-full blocking
set timeout 5
expect {
  timeout {}
  eof {}
}
send "I need you to spawn a subagent. Call the Agent tool with subagent_type Explore and have it investigate the project structure and find all Python files. You MUST use the Agent tool for this, not Glob or Grep directly.\\r"
# Drain pty output for 70s while model + subagent run
set timeout 70
expect {
  timeout {}
  eof {}
}
send "/exit\\r"
expect eof
"""


def get_log_dirs() -> set[str]:
    if not HTTP_LOGS.exists():
        return set()
    return {str(p) for p in HTTP_LOGS.iterdir() if p.is_dir()}


def find_all_requests(new_dirs: list[Path]) -> list[tuple[Path, int]]:
    """Return deduplicated request.json files, preserving chronological order.

    First entry is the parent agent (earliest API call). Subsequent entries
    are subagents. Deduplicates by system prompt content hash so multiple
    turns from the same agent collapse to one entry.
    """
    results = []
    seen = set()
    # new_dirs already sorted chronologically; glob within each is alphabetical
    # (001-request.json before 002-request.json), so iteration order = time order
    for d in new_dirs:
        for req_path in sorted(d.glob("*-request.json")):
            try:
                req = json.loads(req_path.read_text())
                texts = [
                    s.get("text", "")
                    for s in req.get("system", [])
                    if s.get("type") == "text"
                ]
                content = "\n".join(texts)
                h = hashlib.md5(content.encode()).hexdigest()
                if h in seen:
                    continue
                seen.add(h)
                results.append((req_path, len(content)))
            except (json.JSONDecodeError, OSError):
                continue
    return results


def extract_request(req_path: Path, out_dir: Path, file_prefix: str = "") -> dict:
    """Extract one request's system prompt, request body, and summary.

    Returns the summary dict.
    """
    req = json.loads(req_path.read_text())
    blocks = [s for s in req.get("system", []) if s.get("type") == "text"]
    texts = [s["text"] for s in blocks]
    content = "\n\n---BLOCK_SEPARATOR---\n\n".join(texts)

    (out_dir / f"{file_prefix}system.txt").write_text(content)

    if "metadata" in req:
        req["metadata"] = {k: "<redacted>" for k in req["metadata"]}
    (out_dir / f"{file_prefix}request.json").write_text(json.dumps(req, indent=2))

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
    (out_dir / f"{file_prefix}summary.json").write_text(json.dumps(summary, indent=2))

    return summary


def spawn_claude(
    extra_args: list[str],
    model: str = "haiku",
    output_style: str | None = None,
    subagent: bool = False,
) -> None:
    script = EXPECT_SCRIPT_SUBAGENT if subagent else EXPECT_SCRIPT

    exp_file = tempfile.NamedTemporaryFile(
        mode="w", suffix=".exp", prefix="capture-", delete=False
    )
    exp_file.write(script)
    exp_file.close()

    env = os.environ.copy()
    env["NODE_OPTIONS"] = f"--require {INTERCEPT}"

    # Run from a temp dir with its own .claude/settings.local.json so we
    # never touch the real repo's config. git init so interactive mode works.
    work_dir = tempfile.mkdtemp(prefix="capture-cwd-")
    subprocess.run(["git", "init", "-q", work_dir], capture_output=True)
    settings_dir = Path(work_dir) / ".claude"
    settings_dir.mkdir()
    settings = {}
    if output_style is not None:
        settings["outputStyle"] = output_style
    (settings_dir / "settings.local.json").write_text(json.dumps(settings))

    # Subagent mode: seed files so it looks like a real project worth exploring
    if subagent:
        src = Path(work_dir) / "src"
        src.mkdir()
        for name in ["main.py", "utils.py", "config.py", "models.py", "api.py"]:
            (src / name).write_text(f"# {name}\ndef run(): pass\n")
        tests = Path(work_dir) / "tests"
        tests.mkdir()
        (tests / "test_main.py").write_text("import src.main\n")
        (Path(work_dir) / "README.md").write_text("# Example Project\n")
        (Path(work_dir) / "setup.py").write_text("from setuptools import setup\n")

    timeout = 130 if subagent else 35

    try:
        subprocess.run(
            [
                "expect",
                "-f",
                exp_file.name,
                "--",
                "claude",
                "--model",
                model,
                *extra_args,
            ],
            env=env,
            cwd=work_dir,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        pass
    finally:
        os.unlink(exp_file.name)
        shutil.rmtree(work_dir, ignore_errors=True)


def main() -> None:
    extra_args = sys.argv[1:]

    # Our flags, not passed to claude
    model = "haiku"
    if "--capture-model" in extra_args:
        idx = extra_args.index("--capture-model")
        model = extra_args[idx + 1]
        extra_args = extra_args[:idx] + extra_args[idx + 2:]

    output_style: str | None = None
    if "--capture-output-style" in extra_args:
        idx = extra_args.index("--capture-output-style")
        output_style = extra_args[idx + 1]
        extra_args = extra_args[:idx] + extra_args[idx + 2:]

    subagent = False
    if "--subagent" in extra_args:
        idx = extra_args.index("--subagent")
        subagent = True
        extra_args = extra_args[:idx] + extra_args[idx + 1:]

    # Subagent mode: force "default" output style to avoid output-style hooks
    # (e.g. pre_output.record) that add Bash tool calls before the Agent call,
    # which block on permission prompts that nobody answers.
    if subagent and output_style is None:
        output_style = "default"

    before = get_log_dirs()
    spawn_claude(extra_args, model=model, output_style=output_style, subagent=subagent)
    after = get_log_dirs()

    new_dirs = [Path(d) for d in sorted(after - before)]
    if not new_dirs:
        print("ERROR: No API calls captured.", file=sys.stderr)
        sys.exit(1)

    all_reqs = find_all_requests(new_dirs)
    if not all_reqs:
        print("ERROR: No system prompt found in captured requests.", file=sys.stderr)
        sys.exit(1)

    if OUT_DIR.exists():
        shutil.rmtree(OUT_DIR)
    OUT_DIR.mkdir(parents=True)

    # Extract main prompt (largest system prompt)
    main_summary = extract_request(all_reqs[0][0], OUT_DIR)
    content = (OUT_DIR / "system.txt").read_text()
    print(content)

    # Extract subagent prompts
    subagent_summaries = []
    if subagent and len(all_reqs) > 1:
        sub_dir = OUT_DIR / "subagents"
        sub_dir.mkdir()
        for i, (req_path, _) in enumerate(all_reqs[1:], 1):
            prefix = f"{i:03d}"
            s = extract_request(req_path, sub_dir, file_prefix=f"{prefix}-")
            subagent_summaries.append(s)
            sub_content = (sub_dir / f"{prefix}-system.txt").read_text()
            print(f"\n\n===SUBAGENT {i} (model: {s.get('model')})===\n\n{sub_content}")
    elif subagent:
        print(
            "WARNING: --subagent specified but no subagent calls captured.",
            file=sys.stderr,
        )

    n_sub = len(subagent_summaries)
    print(
        f"\n--- Captured main: {main_summary['block_count']} blocks, "
        f"{main_summary['total_chars']} chars (model: {main_summary.get('model')})"
        f"{f', {n_sub} subagent(s)' if subagent else ''} ---",
        file=sys.stderr,
    )


if __name__ == "__main__":
    main()
