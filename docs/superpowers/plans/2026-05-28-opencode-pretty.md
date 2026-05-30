# opencode-pretty Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add `agent-tools opencode-pretty <session-id>` to pretty-print opencode session exports using the opencode binary and cc-pretty-compatible rendering helpers.

**Architecture:** Add a Python `claude_config.opencode_pretty` module that shells out to `opencode export <session-id>`, parses the exported JSON, and renders a transcript using shared `cc_pretty.render` helpers. Add a Rust `agent-tools` forwarding subcommand that invokes the Python module through the existing `uv_run` path.

**Tech Stack:** Python 3.14, argparse, subprocess, pytest, Rust clap, Cargo integration tests, existing `claude_config.cc_pretty` rendering utilities.

---

## File Structure

- Create `src/claude_config/opencode_pretty/__init__.py`: package marker.
- Create `src/claude_config/opencode_pretty/main.py`: CLI, opencode export retrieval, JSON parsing, transcript rendering, and agent chunk output.
- Create `tests/test_opencode_pretty.py`: Python unit tests for parsing, rendering, command invocation, error handling, and agent output chunking behavior.
- Modify `agent-tools/src/main.rs`: add `opencode-pretty` subcommand and dispatch to `python3 -m claude_config.opencode_pretty.main`.
- Modify `agent-tools/tests/opencode_test.rs`: add a help-surface test that proves the Rust CLI exposes `opencode-pretty` without invoking `uv`.
- Modify `CLAUDE.md`: document the new `agent-tools opencode-pretty` command.

Do not read opencode storage files or databases directly. All session retrieval must go through `opencode export`.

---

### Task 1: Python Parser And Renderer Tests

**Files:**
- Create: `tests/test_opencode_pretty.py`

- [ ] **Step 1: Write failing Python tests**

Create `tests/test_opencode_pretty.py` with this complete content:

```python
import json
import subprocess

import pytest

from claude_config.opencode_pretty import main as op


def sample_export() -> dict:
    return {
        "info": {
            "id": "ses_1234567890abcdef",
            "slug": "bright-fox",
            "directory": "/workspace/project",
            "title": "Test Session",
            "version": "1.15.5+test",
            "model": {
                "id": "gpt-5.5",
                "providerID": "openai",
                "variant": "xhigh",
            },
        },
        "messages": [
            {
                "info": {
                    "role": "user",
                    "time": {"created": 1779940742548},
                    "id": "msg_user",
                    "sessionID": "ses_1234567890abcdef",
                },
                "parts": [
                    {
                        "type": "text",
                        "text": "hello from user",
                        "id": "prt_user_text",
                    }
                ],
            },
            {
                "info": {
                    "role": "assistant",
                    "time": {"created": 1779940742555, "completed": 1779940751760},
                    "finish": "stop",
                    "modelID": "gpt-5.5",
                    "providerID": "openai",
                    "tokens": {
                        "input": 99,
                        "output": 142,
                        "reasoning": 305,
                        "cache": {"read": 14336, "write": 0},
                    },
                    "id": "msg_assistant",
                    "sessionID": "ses_1234567890abcdef",
                },
                "parts": [
                    {
                        "type": "reasoning",
                        "text": "private chain summary",
                        "time": {"start": 1779940743450, "end": 1779940749791},
                        "id": "prt_reasoning",
                    },
                    {
                        "type": "tool",
                        "tool": "bash",
                        "callID": "call_abc123",
                        "state": {
                            "status": "completed",
                            "input": {"command": "pwd", "description": "print cwd"},
                            "output": "/workspace/project\n",
                            "title": "pwd",
                            "time": {"start": 1779940751606, "end": 1779940751620},
                        },
                        "id": "prt_tool",
                    },
                    {
                        "type": "text",
                        "text": "assistant response",
                        "id": "prt_assistant_text",
                    },
                    {
                        "type": "step-finish",
                        "reason": "stop",
                        "tokens": {"input": 1, "output": 2},
                        "id": "prt_step_finish",
                    },
                ],
            },
        ],
    }


def render_sample(**kwargs) -> str:
    args = op.RenderOptions(
        tool_max=kwargs.get("tool_max", 200),
        truncate_input=kwargs.get("truncate_input", False),
        show_thinking=kwargs.get("show_thinking", True),
    )
    return op.render_export(sample_export(), args)


def test_parse_export_stdout_skips_status_prefix() -> None:
    payload = {"info": {"id": "ses_1"}, "messages": []}
    stdout = "Exporting session: ses_1\n" + json.dumps(payload)

    assert op.parse_export_stdout(stdout) == payload


def test_parse_export_stdout_rejects_missing_json() -> None:
    with pytest.raises(ValueError, match="does not contain JSON"):
        op.parse_export_stdout("Exporting session: ses_1\n")


def test_render_export_includes_header_turns_reasoning_and_tool() -> None:
    output = render_sample()

    assert "session: Test Session" in output
    assert "id: ses_1234" in output
    assert "model: openai/gpt-5.5/xhigh" in output
    assert "cwd: /workspace/project" in output
    assert "┌ User" in output
    assert "hello from user" in output
    assert "┌ Assistant" in output
    assert "private chain summary" in output
    assert "▶ bash" in output
    assert "call_abc123" in output
    assert "command: pwd" in output
    assert "◀ result" in output
    assert "/workspace/project" in output
    assert "assistant response" in output


def test_render_export_hides_reasoning_when_no_thinking() -> None:
    output = render_sample(show_thinking=False)

    assert "private chain summary" not in output
    assert "[reasoning:" in output


def test_render_export_truncates_tool_output_and_optionally_input() -> None:
    data = sample_export()
    tool = data["messages"][1]["parts"][1]
    tool["state"]["input"] = {"command": "x" * 80}
    tool["state"]["output"] = "y" * 80

    full_input = op.render_export(
        data,
        op.RenderOptions(tool_max=20, truncate_input=False, show_thinking=True),
    )
    truncated_input = op.render_export(
        data,
        op.RenderOptions(tool_max=20, truncate_input=True, show_thinking=True),
    )

    assert "[60 more chars]" in full_input
    assert "[60 more chars]" in truncated_input
    assert "[69 more chars]" not in full_input
    assert "[69 more chars]" in truncated_input


def test_fetch_export_invokes_opencode_binary(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = []

    def fake_run(cmd, text, capture_output, check):
        calls.append((cmd, text, capture_output, check))
        return subprocess.CompletedProcess(cmd, 0, stdout=json.dumps(sample_export()), stderr="")

    monkeypatch.setattr(op.subprocess, "run", fake_run)

    assert op.fetch_export("ses_123")["info"]["id"] == "ses_1234567890abcdef"
    assert calls == [(["opencode", "export", "ses_123"], True, True, False)]


def test_fetch_export_exits_with_opencode_status(monkeypatch: pytest.MonkeyPatch, capsys) -> None:
    def fake_run(cmd, text, capture_output, check):
        return subprocess.CompletedProcess(cmd, 7, stdout="", stderr="no session\n")

    monkeypatch.setattr(op.subprocess, "run", fake_run)

    with pytest.raises(SystemExit) as exc:
        op.fetch_export("missing")

    assert exc.value.code == 7
    assert "no session" in capsys.readouterr().err
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
uv run pytest tests/test_opencode_pretty.py -q
```

Expected: FAIL with `ModuleNotFoundError: No module named 'claude_config.opencode_pretty'`.

---

### Task 2: Python opencode-pretty Implementation

**Files:**
- Create: `src/claude_config/opencode_pretty/__init__.py`
- Create: `src/claude_config/opencode_pretty/main.py`
- Test: `tests/test_opencode_pretty.py`

- [ ] **Step 1: Add the package marker**

Create `src/claude_config/opencode_pretty/__init__.py` with this content:

```python
"""Pretty-print opencode session exports."""
```

- [ ] **Step 2: Add the initial implementation**

Create `src/claude_config/opencode_pretty/main.py` with this complete content:

```python
"""Pretty-print an opencode session export.

Usage: opencode-pretty <session-id> [--tool-max N] [--truncate-input]
                       [--no-color] [--no-thinking] [--agent]
"""

from __future__ import annotations

import argparse
import io
import json
import os
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from claude_config.cc_pretty.render import (
    C,
    fmt_duration,
    fmt_tool_input,
    ind,
    is_truncated,
    separator,
    trunc,
)


@dataclass(frozen=True)
class RenderOptions:
    tool_max: int = 200
    truncate_input: bool = False
    show_thinking: bool = True


def parse_export_stdout(stdout: str) -> dict[str, Any]:
    start = stdout.find("{")
    if start == -1:
        raise ValueError("opencode export output does not contain JSON")
    try:
        data = json.loads(stdout[start:])
    except json.JSONDecodeError as exc:
        raise ValueError(f"failed to parse opencode export JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError("opencode export JSON root is not an object")
    return data


def fetch_export(session_id: str) -> dict[str, Any]:
    result = subprocess.run(
        ["opencode", "export", session_id],
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        if result.stderr:
            print(result.stderr, file=sys.stderr, end="" if result.stderr.endswith("\n") else "\n")
        else:
            print(f"opencode export failed with exit code {result.returncode}", file=sys.stderr)
        raise SystemExit(result.returncode)
    try:
        return parse_export_stdout(result.stdout)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1) from exc


def fmt_time_ms(value: Any) -> str:
    if not isinstance(value, int | float):
        return ""
    dt = datetime.fromtimestamp(value / 1000, tz=timezone.utc)
    return dt.strftime("%H:%M:%S")


def fmt_model(info: dict[str, Any]) -> str:
    model = info.get("model")
    if isinstance(model, dict):
        provider = model.get("providerID") or ""
        model_id = model.get("id") or model.get("modelID") or ""
        variant = model.get("variant") or ""
    else:
        provider = info.get("providerID") or ""
        model_id = info.get("modelID") or ""
        variant = info.get("variant") or ""
    parts = [str(x) for x in (provider, model_id, variant) if x]
    return "/".join(parts)


def fmt_tokens(tokens: Any) -> str:
    if not isinstance(tokens, dict):
        return ""
    parts: list[str] = []
    if tokens.get("input") is not None:
        parts.append(f"in:{int(tokens['input']):,}")
    if tokens.get("output") is not None:
        parts.append(f"out:{int(tokens['output']):,}")
    if tokens.get("reasoning"):
        parts.append(f"reasoning:{int(tokens['reasoning']):,}")
    cache = tokens.get("cache")
    if isinstance(cache, dict):
        if cache.get("read"):
            parts.append(f"cached:{int(cache['read']):,}")
        if cache.get("write"):
            parts.append(f"cache_write:{int(cache['write']):,}")
    return " ".join(parts)


def render_export(data: dict[str, Any], options: RenderOptions) -> str:
    lines: list[str] = []
    header = render_session_header(data.get("info", {}))
    if header:
        lines.append(header)

    for message in data.get("messages", []):
        if not isinstance(message, dict):
            continue
        rendered = render_message(message, options)
        if rendered:
            lines.append(separator())
            lines.append(rendered)
    lines.append(separator())
    return "\n".join(lines) + "\n"


def render_session_header(info: Any) -> str:
    if not isinstance(info, dict):
        return ""
    parts: list[str] = []
    title = info.get("title") or info.get("slug")
    if title:
        parts.append(f"session: {title}")
    session_id = info.get("id")
    if session_id:
        parts.append(f"id: {str(session_id)[:8]}")
    version = info.get("version")
    if version:
        parts.append(f"v{version}")
    model = fmt_model(info)
    if model:
        parts.append(f"model: {model}")
    directory = info.get("directory")
    if directory:
        parts.append(f"cwd: {directory}")
    return f"{C.DIM}{'  '.join(parts)}{C.RESET}" if parts else ""


def render_message(message: dict[str, Any], options: RenderOptions) -> str:
    info = message.get("info") if isinstance(message.get("info"), dict) else {}
    role = info.get("role") or "unknown"
    ts = fmt_time_ms((info.get("time") or {}).get("created") if isinstance(info.get("time"), dict) else None)
    if role == "user":
        return render_user_message(message, ts)
    if role == "assistant":
        return render_assistant_message(message, info, ts, options)
    return ""


def render_user_message(message: dict[str, Any], ts: str) -> str:
    lines = [f"{C.USER}┌ User{C.RESET}  {C.TIMESTAMP}{ts}{C.RESET}"]
    for part in message.get("parts", []):
        if isinstance(part, dict) and part.get("type") == "text":
            lines.append(ind(str(part.get("text") or ""), "  "))
    return "\n".join(lines) if len(lines) > 1 else ""


def render_assistant_message(
    message: dict[str, Any],
    info: dict[str, Any],
    ts: str,
    options: RenderOptions,
) -> str:
    model = fmt_model(info)
    model_tag = f"  {C.DIM}[{model}]{C.RESET}" if model else ""
    finish = info.get("finish") or ""
    finish_tag = f"  {C.DIM}finish:{finish}{C.RESET}" if finish and finish != "stop" else ""
    token_text = fmt_tokens(info.get("tokens"))
    token_tag = f"  {C.DIM}[{token_text}]{C.RESET}" if token_text else ""
    lines = [f"{C.ASSISTANT}┌ Assistant{C.RESET}{model_tag}  {C.TIMESTAMP}{ts}{C.RESET}{finish_tag}{token_tag}"]

    for part in message.get("parts", []):
        if not isinstance(part, dict):
            continue
        part_type = part.get("type")
        if part_type == "reasoning":
            rendered = render_reasoning(part, options)
        elif part_type == "tool":
            rendered = render_tool(part, options)
        elif part_type == "text":
            rendered = ind(str(part.get("text") or ""), "  ")
        else:
            rendered = ""
        if rendered:
            lines.append(rendered)
    return "\n".join(lines) if len(lines) > 1 else ""


def render_reasoning(part: dict[str, Any], options: RenderOptions) -> str:
    text = str(part.get("text") or "")
    if not text:
        return ""
    if not options.show_thinking:
        return f"{C.THINKING}  [reasoning: {len(text)} chars]{C.RESET}"
    prefix = C.THINKING + "  │ " + C.RESET
    body = "\n".join(prefix + line for line in text.splitlines())
    return (
        f"{C.THINKING}  ╭─ reasoning ────────────────{C.RESET}\n"
        f"{body}\n"
        f"{C.THINKING}  ╰────────────────────────────{C.RESET}"
    )


def render_tool(part: dict[str, Any], options: RenderOptions) -> str:
    state = part.get("state") if isinstance(part.get("state"), dict) else {}
    name = str(part.get("tool") or "?")
    call_id = str(part.get("callID") or "")
    id_suffix = f"  {C.DIM}({call_id}){C.RESET}" if call_id else ""
    status = state.get("status") or ""
    title = state.get("title") or ""
    status_suffix = f"  {C.DIM}[{status}]{C.RESET}" if status else ""
    title_suffix = f"  {C.DIM}{title}{C.RESET}" if title else ""
    lines = [f"{C.TOOL}  ▶ {name}{C.RESET}{id_suffix}{status_suffix}{title_suffix}"]

    input_max = options.tool_max if options.truncate_input else sys.maxsize
    tool_input = state.get("input")
    if tool_input not in (None, ""):
        input_text = fmt_tool_input(tool_input) if isinstance(tool_input, dict) else str(tool_input)
        lines.append(ind(trunc(input_text, input_max), "    "))

    output = state.get("output")
    if output not in (None, ""):
        output_text = str(output)
        result_label = "✗ error" if status == "error" else "◀ result"
        result_color = C.ERROR if status == "error" else C.RESULT
        time_text = fmt_tool_duration(state.get("time"))
        time_suffix = f"  {C.DIM}{time_text}{C.RESET}" if time_text else ""
        lines.append(f"{result_color}  {result_label}{C.RESET}{time_suffix}")
        lines.append(ind(trunc(output_text, options.tool_max), "    "))
        if is_truncated(output_text, options.tool_max):
            lines.append(f"    {C.HINT}# output truncated to {options.tool_max} chars{C.RESET}")
    return "\n".join(lines)


def fmt_tool_duration(time_info: Any) -> str:
    if not isinstance(time_info, dict):
        return ""
    start = time_info.get("start")
    end = time_info.get("end")
    if not isinstance(start, int | float) or not isinstance(end, int | float):
        return ""
    if end < start:
        return ""
    return fmt_duration(end - start)


def emit_agent_output(output: str, session_id: str) -> None:
    bash_limit = int(os.environ.get("BASH_MAX_OUTPUT_LENGTH", "30000")) * 4 // 5
    if len(output) <= bash_limit:
        sys.stdout.write(output)
        return

    read_max_tokens = int(os.environ.get("CLAUDE_CODE_FILE_READ_MAX_OUTPUT_TOKENS", "25000"))
    chunk_chars = min(read_max_tokens * 2, 200_000)
    lines = output.split("\n")
    chunks: list[tuple[list[str], int]] = []
    current: list[str] = []
    current_size = 0
    chunk_start = 1

    for lineno, line in enumerate(lines, 1):
        line_len = len(line) + 1
        if current_size + line_len > chunk_chars and current:
            chunks.append((current, chunk_start))
            current = []
            current_size = 0
            chunk_start = lineno
        current.append(line)
        current_size += line_len
    if current:
        chunks.append((current, chunk_start))

    prefix = session_id[:8] or "session"
    infos: list[tuple[str, int, int, int]] = []
    for i, (chunk_lines, start) in enumerate(chunks, 1):
        path = f"/tmp/opencode-pretty-{prefix}-{i}.txt"
        content = "\n".join(chunk_lines)
        with open(path, "w") as f:
            f.write(content)
        end = start + len(chunk_lines) - 1
        infos.append((path, len(content), start, end))

    print(f"Rendered {len(output):,} chars, {len(lines)} lines across {len(infos)} files.")
    print(f"Read all {len(infos)} files in parallel:")
    for path, chars, start, end in infos:
        print(f"  {path} ({chars:,} chars, lines {start}-{end})")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Pretty-print opencode session exports")
    parser.add_argument("session_id", help="opencode session ID to export and render")
    parser.add_argument(
        "--tool-max",
        type=int,
        default=200,
        help="Max chars for tool output (default: 200). Tool input is shown in full unless --truncate-input is set.",
    )
    parser.add_argument(
        "--truncate-input",
        action="store_true",
        help="Also truncate tool input to --tool-max chars (full by default)",
    )
    parser.add_argument("--no-color", action="store_true", help="Disable ANSI colors")
    parser.add_argument(
        "--no-thinking",
        action="store_true",
        help="Collapse reasoning blocks to single-line summaries",
    )
    parser.add_argument(
        "--agent",
        action="store_true",
        help="Agent-friendly output: if small enough, print directly; otherwise write chunk files to /tmp. Implies --no-color.",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.no_color or args.agent:
        C.disable()

    data = fetch_export(args.session_id)
    output = render_export(
        data,
        RenderOptions(
            tool_max=args.tool_max,
            truncate_input=args.truncate_input,
            show_thinking=not args.no_thinking,
        ),
    )

    if args.agent:
        emit_agent_output(output, args.session_id)
    else:
        sys.stdout.write(output)


if __name__ == "__main__":
    main()
```

- [ ] **Step 3: Run Python tests**

Run:

```bash
uv run pytest tests/test_opencode_pretty.py -q
```

Expected: PASS for all tests in `tests/test_opencode_pretty.py`.

---

### Task 3: Agent Chunk Output Test

**Files:**
- Modify: `tests/test_opencode_pretty.py`
- Test: `tests/test_opencode_pretty.py`

- [ ] **Step 1: Add a focused agent-output test**

Append this test to `tests/test_opencode_pretty.py`:

```python

def test_emit_agent_output_writes_chunks_when_large(monkeypatch: pytest.MonkeyPatch, tmp_path, capsys) -> None:
    monkeypatch.setenv("BASH_MAX_OUTPUT_LENGTH", "20")
    monkeypatch.setenv("CLAUDE_CODE_FILE_READ_MAX_OUTPUT_TOKENS", "5")

    written: dict[str, str] = {}

    class FakeFile:
        def __init__(self, path: str) -> None:
            self.path = path
            self.parts: list[str] = []

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            written[self.path] = "".join(self.parts)
            return False

        def write(self, content: str) -> None:
            self.parts.append(content)

    def fake_open(path: str, mode: str):
        assert mode == "w"
        assert path.startswith("/tmp/opencode-pretty-ses_abc-")
        return FakeFile(path)

    monkeypatch.setattr(op, "open", fake_open, raising=False)

    op.emit_agent_output("line-one\nline-two\nline-three\n", "ses_abcdef123456")

    stdout = capsys.readouterr().out
    assert "Rendered" in stdout
    assert "Read all" in stdout
    assert written
    assert any("line-one" in content for content in written.values())
```

- [ ] **Step 2: Run Python tests**

Run:

```bash
uv run pytest tests/test_opencode_pretty.py -q
```

Expected: PASS for all tests in `tests/test_opencode_pretty.py`.

---

### Task 4: Rust agent-tools Subcommand

**Files:**
- Modify: `agent-tools/src/main.rs`
- Modify: `agent-tools/tests/opencode_test.rs`

- [ ] **Step 1: Add a failing Rust CLI help test**

Append this test to `agent-tools/tests/opencode_test.rs`:

```rust

#[test]
fn help_lists_opencode_pretty_subcommand() {
    let out = Command::new(bin()).arg("--help").output().unwrap();

    assert!(
        out.status.success(),
        "stderr: {}",
        String::from_utf8_lossy(&out.stderr)
    );
    let stdout = String::from_utf8_lossy(&out.stdout);
    assert!(stdout.contains("opencode-pretty"), "stdout: {stdout}");
}
```

- [ ] **Step 2: Run the failing Rust test**

Run:

```bash
cd agent-tools && cargo test help_lists_opencode_pretty_subcommand
```

Expected: FAIL because `opencode-pretty` is not listed in help yet.

- [ ] **Step 3: Add the Rust subcommand enum variant**

In `agent-tools/src/main.rs`, add this variant after the existing `CcPrettyIntercept` variant:

```rust
    /// Pretty-print an opencode session export
    #[command(name = "opencode-pretty")]
    OpencodePretty {
        /// Session ID and arguments forwarded to opencode-pretty
        #[arg(trailing_var_arg = true, allow_hyphen_values = true)]
        args: Vec<String>,
    },
```

- [ ] **Step 4: Add Rust dispatch**

In `agent-tools/src/main.rs`, add this match arm after the existing `Cmd::CcPrettyIntercept { args }` arm:

```rust
                Cmd::OpencodePretty { args } => {
                    uv_run(
                        &root,
                        &root,
                        &["python3", "-m", "claude_config.opencode_pretty.main"],
                        &args,
                    );
                }
```

- [ ] **Step 5: Run the Rust help test**

Run:

```bash
cd agent-tools && cargo test help_lists_opencode_pretty_subcommand
```

Expected: PASS.

---

### Task 5: Documentation

**Files:**
- Modify: `CLAUDE.md`

- [ ] **Step 1: Add command documentation**

In `CLAUDE.md`, add this bullet immediately after the existing `agent-tools cc-pretty [args]` bullet:

```markdown
- `agent-tools opencode-pretty <session-id> [args]` — pretty-print an opencode session export by running `opencode export <session-id>` and rendering the transcript in a cc-pretty-like format
```

- [ ] **Step 2: Run a docs sanity check**

Run:

```bash
git diff -- CLAUDE.md
```

Expected: diff contains exactly one new bullet in the `agent-tools/` command list.

---

### Task 6: End-To-End Verification

**Files:**
- Verify all modified files.

- [ ] **Step 1: Run Python tests**

Run:

```bash
uv run pytest tests/test_opencode_pretty.py -q
```

Expected: PASS.

- [ ] **Step 2: Run full Python test suite**

Run:

```bash
uv run pytest -q
```

Expected: PASS.

- [ ] **Step 3: Run Rust tests**

Run:

```bash
cd agent-tools && cargo test
```

Expected: PASS.

- [ ] **Step 4: Build agent-tools**

Run:

```bash
cd agent-tools && cargo build --release
```

Expected: PASS and binary exists at `agent-tools/target/release/agent-tools`.

- [ ] **Step 5: Smoke-test help through the built binary**

Run:

```bash
./agent-tools/target/release/agent-tools opencode-pretty --help
```

Expected: output includes `Pretty-print opencode session exports`, `--tool-max`, `--truncate-input`, `--no-color`, `--no-thinking`, and `--agent`.

- [ ] **Step 6: Smoke-test against a real recent session if available**

Run:

```bash
session_id=$(opencode session list --format json --max-count 1 | python3 -c 'import json,sys; data=json.load(sys.stdin); print(data[0]["id"] if data else "")')
if [ -n "$session_id" ]; then ./agent-tools/target/release/agent-tools --root /root/claude-config-work2 opencode-pretty "$session_id" --no-color --tool-max 120; fi
```

Expected: if a recent opencode session exists, output starts with a session header and includes at least one rendered `User` or `Assistant` block.

---

## Execution Notes

- Do not run `install.sh` from this worktree.
- Do not commit unless the user explicitly asks for commits; inspect `git diff` instead at the end.
- Keep unknown opencode part types hidden by default.
- Keep all session data retrieval behind `opencode export <session-id>`.

## Self-Review

- Spec coverage: command surface is covered by Tasks 2 and 4; opencode binary data retrieval is covered by Task 2 tests and implementation; cc-pretty-like rendering is covered by Task 2; error handling is covered by Task 2; agent output is covered by Task 3; docs and verification are covered by Tasks 5 and 6.
- Placeholder scan: no placeholder markers or undefined implementation steps remain.
- Type consistency: `RenderOptions`, `parse_export_stdout`, `fetch_export`, `render_export`, and `emit_agent_output` names are introduced before tests rely on them.
