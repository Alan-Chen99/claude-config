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

import anthropic

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
# {message} is replaced at runtime with the agent-type-specific prompt.
EXPECT_SCRIPT_SUBAGENT = """\
set timeout 120
set env(CLAUDECODE) ""
unset env(CLAUDECODE)
spawn {{*}}$argv
sleep 2
send "\\r"
# Use expect (not sleep) to consume pty output and prevent buffer-full blocking
set timeout 5
expect {{
  timeout {{}}
  eof {{}}
}}
send "{message}\\r"
# Drain pty output for 70s while model + subagent run
set timeout 70
expect {{
  timeout {{}}
  eof {{}}
}}
send "/exit\\r"
expect eof
"""

SUBAGENT_MESSAGES = {
    "Explore": (
        "I need you to spawn a subagent. Call the Agent tool with "
        "subagent_type Explore and have it investigate the project structure "
        "and find all Python files. You MUST use the Agent tool for this, "
        "not Glob or Grep directly."
    ),
    "general-purpose": (
        "I need you to spawn a subagent. Call the Agent tool with "
        "subagent_type general-purpose and have it research what programming "
        "languages and frameworks are used in this project. You MUST use the "
        "Agent tool, not Glob or Grep directly."
    ),
}


def get_log_dirs() -> set[str]:
    if not HTTP_LOGS.exists():
        return set()
    return {str(p) for p in HTTP_LOGS.iterdir() if p.is_dir()}


def _strip_cache_control(obj):
    """Remove cache_control fields that count_tokens rejects."""
    if isinstance(obj, dict):
        return {k: _strip_cache_control(v) for k, v in obj.items() if k != "cache_control"}
    elif isinstance(obj, list):
        return [_strip_cache_control(x) for x in obj]
    return obj


def count_tokens(model: str, *, system=None, tools=None) -> int:
    """Count tokens via the Anthropic API (free endpoint).

    Returns the token count for the given system blocks and/or tools.
    Uses a minimal dummy message; the returned count is for the full request.
    """
    client = anthropic.Anthropic()
    kwargs = {"model": model, "messages": [{"role": "user", "content": "x"}]}
    if system is not None:
        kwargs["system"] = _strip_cache_control(system)
    if tools is not None:
        kwargs["tools"] = _strip_cache_control(tools)
    return client.messages.count_tokens(**kwargs).input_tokens


# Baseline tokens for a minimal request (just message "x", no system/tools).
# Computed once per model and cached.
_baseline_cache: dict[str, int] = {}


def _baseline(model: str) -> int:
    if model not in _baseline_cache:
        _baseline_cache[model] = count_tokens(model)
    return _baseline_cache[model]


def find_all_requests(new_dirs: list[Path]) -> list[tuple[Path, int, bool]]:
    """Return deduplicated request.json files, preserving chronological order.

    Each entry is (path, system_tokens, has_tools). Deduplicates by system
    prompt content hash so multiple turns from the same agent collapse to one.
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
                has_tools = len(req.get("tools", [])) > 0
                model = req.get("model", "claude-opus-4-6")
                sys_blocks = req.get("system", [])
                sys_tokens = count_tokens(model, system=sys_blocks) - _baseline(model)
                results.append((req_path, sys_tokens, has_tools))
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

    model = req.get("model", "claude-opus-4-6")
    base = _baseline(model)
    sys_blocks = req.get("system", [])
    tools = req.get("tools", [])

    sys_tokens = count_tokens(model, system=sys_blocks) - base
    block_tokens = [
        count_tokens(model, system=[blk]) - base for blk in blocks
    ]
    tool_tokens = {
        t["name"]: count_tokens(model, tools=[t]) - base for t in tools
    }

    summary = {
        "version": next(
            (s["text"] for s in blocks if "cc_version" in s.get("text", "")), None
        ),
        "model": model,
        "block_count": len(blocks),
        "total_tokens": sys_tokens,
        "blocks": [
            {"index": i, "tokens": block_tokens[i], "preview": s["text"][:200]}
            for i, s in enumerate(blocks)
        ],
        "tools": [t["name"] for t in tools],
        "tool_tokens": tool_tokens,
        "source_request": req_path.name,
    }
    (out_dir / f"{file_prefix}summary.json").write_text(json.dumps(summary, indent=2))

    return summary


def spawn_claude(
    extra_args: list[str],
    model: str = "haiku",
    output_style: str | None = None,
    subagent: str | None = None,
) -> None:
    if subagent:
        message = SUBAGENT_MESSAGES.get(subagent, SUBAGENT_MESSAGES["Explore"])
        script = EXPECT_SCRIPT_SUBAGENT.format(message=message)
    else:
        script = EXPECT_SCRIPT

    exp_file = tempfile.NamedTemporaryFile(
        mode="w", suffix=".exp", prefix="capture-", delete=False
    )
    exp_file.write(script)
    exp_file.close()

    env = os.environ.copy()
    env["NODE_OPTIONS"] = f"--require {INTERCEPT}"

    # Run from a temp dir; use --setting-sources local to isolate from
    # user's global settings (e.g. autoMemoryEnabled: false). git init so
    # interactive mode works.
    work_dir = tempfile.mkdtemp(prefix="capture-cwd-")
    subprocess.run(["git", "init", "-q", work_dir], capture_output=True)
    settings_dir = Path(work_dir) / ".claude"
    settings_dir.mkdir()
    settings = {}
    if output_style is not None:
        settings["outputStyle"] = output_style
    (settings_dir / "settings.local.json").write_text(json.dumps(settings))

    # Add a CLAUDE.md so the capture includes the claudeMd context block
    (Path(work_dir) / "CLAUDE.md").write_text(
        "# Capture Project\n\nPlaceholder CLAUDE.md for system prompt capture.\n"
    )

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
                "--setting-sources",
                "project,local",
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

    subagent: str | None = None
    if "--subagent" in extra_args:
        idx = extra_args.index("--subagent")
        # Optional agent type follows --subagent (default: Explore)
        if idx + 1 < len(extra_args) and not extra_args[idx + 1].startswith("-"):
            subagent = extra_args[idx + 1]
            extra_args = extra_args[:idx] + extra_args[idx + 2:]
        else:
            subagent = "Explore"
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

    # Select main prompt: prefer requests that have tools defined (the main
    # conversation call), falling back to largest system prompt. v2.1.87+ makes
    # a title-generation Haiku call (~250 tokens, no tools) before the main call.
    # With --system-prompt the main call can be smaller than the title-gen call,
    # so size alone is not sufficient — tools presence is the reliable signal.
    main_idx = max(
        range(len(all_reqs)),
        key=lambda i: (all_reqs[i][2], all_reqs[i][1]),  # (has_tools, size)
    )
    main_summary = extract_request(all_reqs[main_idx][0], OUT_DIR)
    content = (OUT_DIR / "system.txt").read_text()
    print(content)

    # Extract subagent prompts (everything except the main prompt)
    subagent_summaries = []
    other_reqs = [r for i, r in enumerate(all_reqs) if i != main_idx]
    if subagent and other_reqs:
        # Filter out preflight/title-gen calls: keep only requests with tools
        # (subagents always have tools) or substantial system prompts (> 2K)
        sub_reqs = [(p, sz) for p, sz, ht in other_reqs if ht or sz > 2000]
        if sub_reqs:
            sub_dir = OUT_DIR / "subagents"
            sub_dir.mkdir()
            for i, (req_path, _) in enumerate(sub_reqs, 1):
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
        f"{main_summary['total_tokens']} tokens (model: {main_summary.get('model')})"
        f"{f', {n_sub} subagent(s)' if subagent else ''} ---",
        file=sys.stderr,
    )


if __name__ == "__main__":
    main()
