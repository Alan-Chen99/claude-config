#!/usr/bin/env python3
"""Capture system prompts from a Claude Code interactive session.

Uses the MITM proxy (scripts/intercept) to intercept API calls via
HTTPS_PROXY. Works with both the Node.js CLI and native binary.

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

Prerequisites:
    The MITM proxy must be running:
        cd scripts/intercept && python3 run-proxy.py
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
INTERCEPT_DIR = SCRIPT_DIR.parent.parent / "scripts" / "intercept"
OUT_DIR = SCRIPT_DIR / "capture-output"

PROXY_PORT = int(os.environ.get("INTERCEPT_PORT", "9160"))
CA_CERT = Path.home() / ".mitmproxy" / "mitmproxy-ca-cert.pem"
PROXY_LOG_DIR = Path.home() / ".claude" / "requests-log" / "proxy"

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


# --- Proxy communication ---


def proxy_counter() -> int:
    """Get the current log counter by scanning log directory."""
    if not PROXY_LOG_DIR.exists():
        return 0
    nums = []
    for f in PROXY_LOG_DIR.glob("*.json"):
        try:
            nums.append(int(f.stem))
        except ValueError:
            continue
    return max(nums) if nums else 0


def proxy_is_running() -> bool:
    import socket

    try:
        with socket.create_connection(("127.0.0.1", PROXY_PORT), timeout=1):
            return True
    except OSError:
        return False


def start_proxy() -> subprocess.Popen:
    """Start the proxy as a subprocess. Returns the Popen handle."""
    import time

    proc = subprocess.Popen(
        [sys.executable, str(INTERCEPT_DIR / "run-proxy.py")],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    for _ in range(30):
        time.sleep(0.2)
        if proxy_is_running():
            return proc
    proc.kill()
    raise RuntimeError("Proxy failed to start within 6 seconds")


# --- Log reading ---


def find_new_logs(start_counter: int) -> list[Path]:
    """Find proxy log files with counter > start_counter."""
    if not PROXY_LOG_DIR.exists():
        return []
    results = []
    for f in sorted(PROXY_LOG_DIR.glob("*.json")):
        m = f.stem
        try:
            n = int(m)
        except ValueError:
            continue
        if n > start_counter:
            results.append(f)
    return results


def find_all_requests(
    log_files: list[Path],
) -> list[tuple[Path, int, bool]]:
    """Return deduplicated requests from proxy log files.

    The proxy logs contain {request: {...}, response: {...}} entries.
    We extract the request body and write it to a temp file so
    extract_request() can read it in the same format as before.

    Each entry is (path_to_request_json, system_chars, has_tools).
    Deduplicates by system prompt content hash.
    """
    results = []
    seen: set[str] = set()
    tmp_dir = Path(tempfile.mkdtemp(prefix="capture-reqs-"))

    for log_path in log_files:
        try:
            entry = json.loads(log_path.read_text())
        except (json.JSONDecodeError, OSError):
            continue

        req = entry.get("request")
        if not req or not isinstance(req, dict):
            continue
        if "system" not in req:
            continue

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

        # Write the request body to a temp file for extract_request()
        req_path = tmp_dir / f"{log_path.stem}-request.json"
        req_path.write_text(json.dumps(req, indent=2))

        has_tools = len(req.get("tools", [])) > 0
        results.append((req_path, len(content), has_tools))

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
    # Route traffic through the MITM proxy
    env["HTTPS_PROXY"] = f"http://127.0.0.1:{PROXY_PORT}"
    env["NODE_EXTRA_CA_CERTS"] = str(CA_CERT)
    # Node.js fetch (undici) requires --use-env-proxy to honor HTTPS_PROXY
    existing_opts = env.get("NODE_OPTIONS", "")
    env["NODE_OPTIONS"] = f"--use-env-proxy {existing_opts}".strip()

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

    # Ensure proxy is running
    proxy_proc = None
    if not proxy_is_running():
        if not (INTERCEPT_DIR / "run-proxy.py").exists():
            print(
                "ERROR: run-proxy.py not found in scripts/intercept/",
                file=sys.stderr,
            )
            sys.exit(1)
        print("Starting intercept proxy...", file=sys.stderr)
        proxy_proc = start_proxy()

    start_counter = proxy_counter()
    if start_counter < 0:
        print("ERROR: Cannot read proxy counter.", file=sys.stderr)
        sys.exit(1)

    spawn_claude(extra_args, model=model, output_style=output_style, subagent=subagent)

    log_files = find_new_logs(start_counter)
    if not log_files:
        print("ERROR: No API calls captured.", file=sys.stderr)
        if proxy_proc:
            proxy_proc.terminate()
        sys.exit(1)

    all_reqs = find_all_requests(log_files)
    if not all_reqs:
        print("ERROR: No system prompt found in captured requests.", file=sys.stderr)
        if proxy_proc:
            proxy_proc.terminate()
        sys.exit(1)

    if OUT_DIR.exists():
        shutil.rmtree(OUT_DIR)
    OUT_DIR.mkdir(parents=True)

    # Select main prompt: prefer requests that have tools defined (the main
    # conversation call), falling back to largest system prompt. v2.1.87+ makes
    # a title-generation Haiku call (~900 chars, no tools) before the main call.
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
                print(
                    f"\n\n===SUBAGENT {i} (model: {s.get('model')})===\n\n{sub_content}"
                )
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

    # Leave proxy running — it's designed to be long-lived
    # Only stop it if we started it AND the user didn't have one already
    # (i.e., never stop it — the user manages the lifecycle)


if __name__ == "__main__":
    main()
