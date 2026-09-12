#!/usr/bin/env python3
"""Capture system prompts from a Claude Code interactive session.

Routes API traffic through the MITM proxy (scripts/intercept/) via
HTTPS_PROXY. Works with both the Node.js CLI and native binary.

Spawns Claude with a real pty via pty.fork() (true interactive mode).
This matters because the system prompt differs between interactive
and -p mode (identity block, gitStatus appending).

Usage:
    ./capture.py                                        # default prompt
    ./capture.py --system-prompt "custom prompt"        # with --system-prompt
    ./capture.py --system-prompt-file /path/to/file     # with --system-prompt-file
    ./capture.py --append-system-prompt "extra"         # with --append-system-prompt
    ./capture.py --subagent                             # capture Explore + general-purpose
    ./capture.py --subagent general-purpose             # capture only general-purpose
    ./capture.py --subagent Explore,general-purpose     # comma-separated list

Output:
    stdout: system prompt text (blocks joined by ---BLOCK_SEPARATOR---)
    capture-output/system.txt     - main system prompt (same as stdout)
    capture-output/request.json   - main API request (metadata redacted)
    capture-output/summary.json   - block structure and tool inventory
    capture-output/subagents/     - subagent prompts (when --subagent)

Prerequisites:
    The MITM proxy must be running (auto-started if not):
        cd scripts/intercept && python3 run-proxy.py
"""

import hashlib
import json
import os
import pty
import re
import select
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import anthropic
from claude_config.config import load as _load_env

_load_env()

SCRIPT_DIR = Path(__file__).resolve().parent
INTERCEPT_DIR = SCRIPT_DIR.parent.parent / "scripts" / "intercept"
OUT_DIR = SCRIPT_DIR / "capture-output"

PROXY_PORT = int(os.environ.get("INTERCEPT_PORT", "9160"))
CA_CERT = Path.home() / ".mitmproxy" / "mitmproxy-ca-cert.pem"

# Token counting (count_tokens API) and child spawn happen in this parent process.
# If parent inherits HTTPS_PROXY (e.g. running inside an intercepted Claude session),
# anthropic SDK calls fail with TLS errors. Child claude gets HTTPS_PROXY set
# explicitly in spawn_claude(), so unsetting in parent is safe.
for _k in ("HTTPS_PROXY", "https_proxy", "HTTP_PROXY", "http_proxy"):
    os.environ.pop(_k, None)
# Proxy writes per-session: ~/.claude/requests-log/{session_id}/NNNN.json
PROXY_LOG_BASE = Path.home() / ".claude" / "requests-log"
_LOG_FILE_RE = re.compile(r"^\d+\.json$")
_BILLING_HEADER_RE = re.compile(r"^x-anthropic-billing-header:.*$", re.MULTILINE)

def _pty_drain(fd: int, timeout: float) -> str:
    """Read all available pty output until timeout, preventing buffer-full blocking."""
    buf = []
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        remaining = max(0.01, deadline - time.monotonic())
        r, _, _ = select.select([fd], [], [], min(remaining, 0.5))
        if r:
            try:
                data = os.read(fd, 4096)
                if not data:
                    break
                buf.append(data.decode("utf-8", errors="replace"))
            except OSError:
                break
    return "".join(buf)

SUBAGENT_MESSAGES = {
    "Explore": (
        "Call the Agent tool with subagent_type Explore and have it "
        "investigate the project structure and find all Python files. "
        "You MUST use the Agent tool, not Glob or Grep directly."
    ),
    "general-purpose": (
        "Call the Agent tool with subagent_type general-purpose and have it "
        "research what programming languages and frameworks are used in this "
        "project. You MUST use the Agent tool, not Glob or Grep directly."
    ),
}

# When --subagent is passed without a name, run this set in one session.
DEFAULT_SUBAGENTS: tuple[str, ...] = ("Explore", "general-purpose")


def build_subagent_message(names: list[str]) -> str:
    if len(names) == 1:
        return f"I need you to spawn a subagent. {SUBAGENT_MESSAGES[names[0]]}"
    bullets = "\n\n".join(
        f"{i + 1}. {SUBAGENT_MESSAGES[n]}" for i, n in enumerate(names)
    )
    return (
        "I need you to spawn subagents in sequence. Run them one at a time, "
        "waiting for each to finish before starting the next.\n\n" + bullets
    )


# --- Token counting ---


def _strip_cache_control(obj):
    """Remove cache_control fields that count_tokens rejects."""
    if isinstance(obj, dict):
        return {k: _strip_cache_control(v) for k, v in obj.items() if k != "cache_control"}
    elif isinstance(obj, list):
        return [_strip_cache_control(x) for x in obj]
    return obj


def _strip_defer_loading(tool: dict) -> dict:
    return {k: v for k, v in tool.items() if k != "defer_loading"}


def count_tokens(model: str, *, system=None, tools=None) -> int:
    """Count tokens via the Anthropic API (free endpoint).

    Returns the token count for the given system blocks and/or tools.
    Uses a minimal dummy message; the returned count is for the full request.
    """
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_TOKEN_COUNT_API_KEY"])
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


# --- Proxy log reading ---


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


def find_new_proxy_logs(start_time: float, child_pid: int) -> list[Path]:
    """Find proxy logs after start_time whose session.pid matches child_pid.

    Filtering by PID is required: concurrent Claude Code sessions also write
    to ~/.claude/requests-log/<session_id>/, and mtime alone would mix their
    traffic into ours.
    """
    if not PROXY_LOG_BASE.exists():
        return []
    matched: list[Path] = []
    for session_dir in PROXY_LOG_BASE.iterdir():
        if not session_dir.is_dir():
            continue
        for f in session_dir.glob("*.json"):
            if not _LOG_FILE_RE.match(f.name):
                continue
            try:
                if f.stat().st_mtime <= start_time:
                    continue
                entry = json.loads(f.read_text())
            except (OSError, json.JSONDecodeError):
                continue
            if entry.get("session", {}).get("pid") == child_pid:
                matched.append(f)
    return sorted(matched, key=lambda p: p.stat().st_mtime)


def find_all_requests_proxy(
    log_files: list[Path],
) -> list[tuple[Path, int, bool, bool]]:
    """Return deduplicated requests from proxy log files.

    Each entry is (path_to_request_json, system_tokens, has_tools, is_subagent).
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
        # The billing header carries per-request fingerprints — cch, cc_prev_req,
        # cc_prompt_id — so hashing it verbatim makes every request unique and
        # dedup collapses to nothing. The whole line is normalized rather than
        # each field, so a newly added fingerprint cannot silently break dedup
        # again.
        norm = _BILLING_HEADER_RE.sub("x-anthropic-billing-header: <normalized>", content)
        h = hashlib.md5(norm.encode()).hexdigest()
        if h in seen:
            continue
        seen.add(h)

        req_path = tmp_dir / f"{log_path.stem}-request.json"
        req_path.write_text(json.dumps(req, indent=2))

        has_tools = len(req.get("tools", [])) > 0
        is_subagent = "cc_is_subagent=true" in content
        model = req.get("model", "claude-opus-4-6")
        sys_blocks = req.get("system", [])
        sys_tokens = count_tokens(model, system=sys_blocks) - _baseline(model)
        results.append((req_path, sys_tokens, has_tools, is_subagent))
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
    # count_tokens rejects a request whose every tool is deferred, so the lone
    # DeferredToolPlaceholder entry is measured with the flag dropped. The
    # definition text is what is being sized; the flag is not part of it.
    tool_tokens = {
        t["name"]: count_tokens(model, tools=[_strip_defer_loading(t)]) - base
        for t in tools
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


CREDENTIALS_FILE = Path.home() / ".claude" / ".credentials.json"

# Rendered by the child when it starts unauthenticated.
AUTH_FAILURE_MARKERS = ("Not logged in", "Login expired", "Please run /login")

# Trust-dialog labels and the cursor glyph that marks the selected one, all
# flattened the way _flatten_pty flattens the screen they are matched against.
TRUST_OPTION = "Yes,Itrustthisfolder"
DECLINE_OPTION = "No,exit"
MENU_CURSOR = "\u276f"

_ANSI_RE = re.compile(r"\x1b\[[0-9;?<>]*[ -/]*[@-~]|\x1b[@-Z\\-_]")


def _has_stored_credentials() -> bool:
    try:
        creds = json.loads(CREDENTIALS_FILE.read_text())
    except (OSError, json.JSONDecodeError):
        return False
    return bool(creds.get("claudeAiOauth", {}).get("accessToken"))


def _flatten_pty(output: str) -> str:
    """Strip escapes and whitespace so column-redrawn text matches literally.

    Claude Code repositions the cursor between words instead of emitting
    spaces, so "Login expired" arrives as "Login\x1b[9Gexpired". Dropping both
    escapes and whitespace makes such fragments comparable.
    """
    return "".join(_ANSI_RE.sub("", output).split())


def _trust_arrow_presses(screen: str) -> int:
    """Down-arrows needed to move the trust dialog's cursor onto the trust option.

    Confirming "No, exit" quits the child before it issues a single API call,
    and that surfaces downstream only as an empty capture with no stated cause.
    Which option starts selected is not a constant: 2.1.235 preselected the
    trust option and a bare Enter accepted it, 2.1.269 preselects "No, exit".
    Reading the cursor off the screen keeps the capture working under either
    order instead of pinning it to one build's default.

    The dialog repaints several times, so the last placement in the buffer is
    the live one.
    """
    flat = _flatten_pty(screen)
    if TRUST_OPTION not in flat:
        return 0  # already-trusted directory: no dialog to answer
    return 1 if flat.rfind(MENU_CURSOR + DECLINE_OPTION) > flat.rfind(
        MENU_CURSOR + TRUST_OPTION
    ) else 0


def _assert_authenticated(output: str) -> None:
    flat = _flatten_pty(output)
    hit = next(
        (m for m in AUTH_FAILURE_MARKERS if "".join(m.split()) in flat), None
    )
    if hit:
        raise RuntimeError(
            f"Spawned Claude session is unauthenticated (pty showed {hit!r}). "
            "No API call was made, so nothing can be captured."
        )


def spawn_claude(
    extra_args: list[str],
    model: str = "haiku",
    output_style: str | None = None,
    subagents: list[str] | None = None,
) -> int:
    env = os.environ.copy()
    # A capture inherits none of the capturing session's own Claude Code
    # configuration. Every CLAUDE_CODE_* variable is a knob that can change what
    # the child's prompt says, and a capture that reads one records this
    # machine's setup rather than the CLI's behaviour -- so committed snapshots
    # stop being comparable to each other, silently and without a diff to show
    # for it. Three that demonstrably do so: CLAUDECODE and
    # CLAUDE_CODE_CHILD_SESSION make the child detect a nested session and stop
    # saving a transcript; CLAUDE_CODE_TMPDIR moves the scratchpad path the
    # prompt prints; CLAUDE_CODE_FORK_SUBAGENT=0 (set by this repo's
    # settings.json since c70788a) swaps the subagent guidance from the `fork`
    # paragraph to the older Agent/Explore bullets. Dropping the prefix wholesale
    # rather than naming knobs keeps the next one from landing unnoticed.
    # CLAUDE_CODE_OAUTH_TOKEN is the exception: it authenticates the child.
    for _var in [k for k in env if k.startswith("CLAUDE_CODE_")]:
        if _var != "CLAUDE_CODE_OAUTH_TOKEN":
            del env[_var]
    env.pop("CLAUDECODE", None)
    # Claude Code strips CLAUDE_CODE_OAUTH_TOKEN from tool subprocess
    # environments, so a capture launched from inside a session inherits no
    # credentials. Without them the child renders "Not logged in" and issues
    # zero API calls, which surfaces downstream as an unexplained empty capture.
    if not env.get("CLAUDE_CODE_OAUTH_TOKEN") and not _has_stored_credentials():
        raise RuntimeError(
            "No Claude credentials available for the spawned session: "
            "CLAUDE_CODE_OAUTH_TOKEN is unset and ~/.claude/.credentials.json "
            "holds no access token. Export CLAUDE_CODE_OAUTH_TOKEN before "
            "running capture.py (see README, 'Credentials')."
        )
    # Route through MITM proxy
    env["HTTPS_PROXY"] = f"http://127.0.0.1:{PROXY_PORT}"
    # Node.js fetch (undici) ignores HTTPS_PROXY unless --use-env-proxy is set.
    # Native binaries respect HTTPS_PROXY directly via system CA store.
    env["NODE_OPTIONS"] = "--use-env-proxy"
    env["NODE_EXTRA_CA_CERTS"] = str(CA_CERT)

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
    if subagents:
        src = Path(work_dir) / "src"
        src.mkdir()
        for name in ["main.py", "utils.py", "config.py", "models.py", "api.py"]:
            (src / name).write_text(f"# {name}\ndef run(): pass\n")
        tests = Path(work_dir) / "tests"
        tests.mkdir()
        (tests / "test_main.py").write_text("import src.main\n")
        (Path(work_dir) / "README.md").write_text("# Example Project\n")
        (Path(work_dir) / "setup.py").write_text("from setuptools import setup\n")

    # Mirror any user-global agent overrides as project-local agents so they
    # are loaded under --setting-sources project,local (which excludes user
    # settings). Lets us test a user-global agent override without dragging in
    # the user's hooks, statusline, ntfy config, etc.
    user_agents_dir = Path.home() / ".claude" / "agents"
    if subagents and user_agents_dir.is_dir():
        project_agents_dir = settings_dir / "agents"
        project_agents_dir.mkdir(exist_ok=True)
        for name in subagents:
            override = user_agents_dir / f"{name}.md"
            if override.exists():
                shutil.copy(override, project_agents_dir / f"{name}.md")

    if subagents:
        message = build_subagent_message(subagents)

    cmd = ["claude", "--model", model, "--setting-sources", "project,local", *extra_args]
    timeout_s = (130 + 90 * (len(subagents) - 1)) if subagents else 60
    deadline = time.monotonic() + timeout_s

    # Use pty.fork() instead of expect. Expect's spawn loses proxy env vars
    # because it re-execs through a shell wrapper; pty.fork + os.execvpe
    # preserves the full environment for the child process.
    pid, fd = pty.fork()
    if pid == 0:
        os.chdir(work_dir)
        os.execvpe(cmd[0], cmd, env)

    transcript: list[str] = []
    try:
        # Accept trust dialog, moving the cursor onto the trust option first
        # when the build starts with "No, exit" selected.
        opening = _pty_drain(fd, 5)
        transcript.append(opening)
        for _ in range(_trust_arrow_presses(opening)):
            os.write(fd, b"\x1b[B")
            time.sleep(0.3)
        os.write(fd, b"\r")

        # Claude Code enables bracketed paste mode. A trailing \r in the same
        # write gets absorbed into the paste payload instead of submitting,
        # so write the message and the submit-Enter as separate writes.
        if subagents:
            transcript.append(_pty_drain(fd, 10))
            os.write(fd, message.encode())
            time.sleep(0.5)
            os.write(fd, b"\r")
            transcript.append(_pty_drain(fd, timeout_s - 20))
        else:
            transcript.append(_pty_drain(fd, 10))
            os.write(fd, b"say exactly: done")
            time.sleep(0.3)
            os.write(fd, b"\r")
            transcript.append(_pty_drain(fd, 30))

        os.write(fd, b"/exit\r")
        transcript.append(_pty_drain(fd, 5))
    except OSError:
        pass
    finally:
        try:
            os.close(fd)
        except OSError:
            pass
        try:
            os.waitpid(pid, 0)
        except ChildProcessError:
            pass
        shutil.rmtree(work_dir, ignore_errors=True)

    _assert_authenticated("".join(transcript))
    return pid


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

    subagents: list[str] | None = None
    if "--subagent" in extra_args:
        idx = extra_args.index("--subagent")
        # Optional value follows --subagent: a single agent name or a
        # comma-separated list. Bare --subagent runs DEFAULT_SUBAGENTS.
        if idx + 1 < len(extra_args) and not extra_args[idx + 1].startswith("-"):
            subagents = [n.strip() for n in extra_args[idx + 1].split(",") if n.strip()]
            extra_args = extra_args[:idx] + extra_args[idx + 2:]
        else:
            subagents = list(DEFAULT_SUBAGENTS)
            extra_args = extra_args[:idx] + extra_args[idx + 1:]

    # Subagent mode: force "default" output style to avoid output-style hooks
    # (e.g. pre_output.record) that add Bash tool calls before the Agent call,
    # which block on permission prompts that nobody answers.
    if subagents and output_style is None:
        output_style = "default"

    # Ensure proxy is running
    proxy_proc = None
    if not proxy_is_running():
        if not (INTERCEPT_DIR / "run-proxy.py").exists():
            print("ERROR: run-proxy.py not found in scripts/intercept/", file=sys.stderr)
            sys.exit(1)
        print("Starting intercept proxy...", file=sys.stderr)
        proxy_proc = start_proxy()

    # Subtract 1s to tolerate clock skew between file mtimes and our wall clock.
    start_time = time.time() - 1
    child_pid = spawn_claude(
        extra_args, model=model, output_style=output_style, subagents=subagents
    )

    log_files = find_new_proxy_logs(start_time, child_pid)
    if not log_files:
        print("ERROR: No API calls captured.", file=sys.stderr)
        if proxy_proc:
            proxy_proc.terminate()
        sys.exit(1)

    all_reqs = find_all_requests_proxy(log_files)
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
    # a title-generation Haiku call (~250 tokens, no tools) before the main call.
    # With --system-prompt the main call can be smaller than the title-gen call,
    # so size alone is not sufficient — tools presence is the reliable signal.
    # Subagent calls also carry tools, and are excluded by their header flag.
    main_idx = max(
        range(len(all_reqs)),
        # (not subagent, has_tools, size)
        key=lambda i: (not all_reqs[i][3], all_reqs[i][2], all_reqs[i][1]),
    )
    main_summary = extract_request(all_reqs[main_idx][0], OUT_DIR)
    content = (OUT_DIR / "system.txt").read_text()
    print(content)

    # Extract subagent prompts. `cc_is_subagent=true` in the billing header is
    # the authoritative marker; size and tool-presence heuristics also match the
    # title-generation call and the security-monitor classifier, which are not
    # subagents.
    subagent_summaries = []
    if subagents:
        sub_reqs = [
            (p, sz) for i, (p, sz, _ht, is_sub) in enumerate(all_reqs)
            if is_sub and i != main_idx
        ]
        if not sub_reqs:
            raise RuntimeError(
                f"--subagent requested {subagents} but no request carried "
                "cc_is_subagent=true; the session never spawned an agent."
            )
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

    n_sub = len(subagent_summaries)
    print(
        f"\n--- Captured main: {main_summary['block_count']} blocks, "
        f"{main_summary['total_tokens']} tokens (model: {main_summary.get('model')})"
        f"{f', {n_sub} subagent(s)' if subagents else ''} ---",
        file=sys.stderr,
    )



if __name__ == "__main__":
    main()
