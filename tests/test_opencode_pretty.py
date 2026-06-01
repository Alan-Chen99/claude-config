from __future__ import annotations

import subprocess
import shutil
import uuid
from pathlib import Path

import pytest

from claude_config.opencode_pretty.main import (
    RenderOptions,
    emit_agent_output,
    fetch_export,
    parse_export_stdout,
    render_export,
)


def sample_export() -> dict:
    return {
        "info": {
            "id": "ses_1234567890abcdef",
            "slug": "parser-work",
            "title": "Parser work",
            "version": "1.15.5+0086a0b",
            "directory": "/root/claude-config-work2",
            "model": {"id": "gpt-5.5", "providerID": "openai", "variant": "xhigh"},
            "time": {"created": 1_700_000_000_123, "updated": 1_700_000_001_456},
        },
        "messages": [
            {
                "info": {
                    "role": "user",
                    "time": {"created": 1_700_000_000_123},
                    "providerID": "anthropic",
                    "modelID": "claude-sonnet-4",
                    "tokens": {"input": 10, "output": 0},
                    "finish": "stop",
                },
                "parts": [{"type": "text", "text": "please inspect this"}],
            },
            {
                "info": {
                    "role": "assistant",
                    "time": {"created": 1_700_000_001_456},
                    "providerID": "anthropic",
                    "modelID": "claude-sonnet-4",
                    "tokens": {"input": 10, "output": 20},
                    "finish": "tool_calls",
                },
                "parts": [
                    {"type": "step-start"},
                    {"type": "reasoning", "text": "I should inspect the file first."},
                    {"type": "text", "text": "I will inspect it."},
                    {
                        "type": "tool",
                        "name": "read",
                        "id": "prt_part_123",
                        "callID": "call_abc",
                        "state": {
                            "status": "completed",
                            "title": "Read /tmp/example.txt",
                            "input": {"filePath": "/tmp/example.txt"},
                            "output": "file contents here",
                            "time": {"start": 1_700_000_001_000, "end": 1_700_000_001_250},
                        },
                    },
                    {"type": "step-finish"},
                    {"type": "unknown", "text": "ignore me"},
                ],
            },
        ],
    }


def test_parse_export_stdout_skips_status_prefix_before_json() -> None:
    parsed = parse_export_stdout('opencode export\nloading session...\n{"id":"ses_1"}')

    assert parsed == {"id": "ses_1"}


def test_parse_export_stdout_raises_when_no_json_object_exists() -> None:
    with pytest.raises(ValueError, match="no JSON object"):
        parse_export_stdout("opencode export\nloading session...")


def test_parse_export_stdout_raises_for_truncated_json_instead_of_nested_object() -> None:
    truncated = 'status prefix\n{"info":{"id":"ses_1"},"messages":[{"info":{"role":"user"}}'

    with pytest.raises(ValueError, match="invalid JSON"):
        parse_export_stdout(truncated)


def test_render_export_includes_session_messages_reasoning_and_tool_details() -> None:
    output = render_export(sample_export(), RenderOptions(no_color=True))

    assert "Session ses_1234567890abcdef" in output
    assert "Parser work" in output
    assert "parser-work" in output
    assert "1.15.5+0086a0b" in output
    assert "/root/claude-config-work2" in output
    assert "openai/gpt-5.5/xhigh" in output
    assert "{'id': 'gpt-5.5'" not in output
    assert "22:13:20" in output
    assert "USER" in output
    assert "please inspect this" in output
    assert "ASSISTANT" in output
    assert "I will inspect it." in output
    assert "reasoning" in output
    assert "I should inspect the file first." in output
    assert "read" in output
    assert "call_abc" in output
    assert "prt_part_123" not in output
    assert "completed" in output
    assert "250ms" in output
    assert "Read /tmp/example.txt" in output
    assert "filePath: /tmp/example.txt" in output
    assert "file contents here" in output
    assert "ignore me" not in output
    assert "step-start" not in output
    assert "step-finish" not in output


def test_render_export_includes_error_tool_state_body() -> None:
    export = sample_export()
    tool_part = export["messages"][1]["parts"][3]
    tool_part["state"] = {
        "status": "error",
        "input": {"filePath": "/tmp/missing.txt"},
        "error": "File not found: /tmp/missing.txt",
    }

    output = render_export(export, RenderOptions(no_color=True))

    assert "error" in output
    assert "File not found: /tmp/missing.txt" in output


def test_render_export_hides_reasoning_body_when_show_thinking_false() -> None:
    output = render_export(sample_export(), RenderOptions(no_color=True, show_thinking=False))

    assert "reasoning hidden" in output
    assert "I should inspect the file first." not in output


def test_render_export_truncates_tool_output_and_input_only_when_requested() -> None:
    export = sample_export()
    tool_state = export["messages"][1]["parts"][3]["state"]
    tool_state["input"] = {"prompt": "x" * 30}
    tool_state["output"] = "y" * 30

    untruncated_input = render_export(
        export,
        RenderOptions(no_color=True, tool_max=10, truncate_input=False),
    )
    truncated_input = render_export(
        export,
        RenderOptions(no_color=True, tool_max=10, truncate_input=True),
    )

    assert "more chars" in untruncated_input
    assert "x" * 30 in untruncated_input
    assert "x" * 30 not in truncated_input


def test_fetch_export_redirects_stdout_to_file_and_captures_stderr(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = []
    stdout_was_writable = False

    def fake_run(*args, **kwargs):
        nonlocal stdout_was_writable
        calls.append((args, kwargs))
        stdout = kwargs["stdout"]
        stdout_was_writable = stdout.writable()
        stdout.write('{"id":"ses_1"}')
        stdout.flush()
        return subprocess.CompletedProcess(args[0], 0, stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)

    assert fetch_export("ses_1") == {"id": "ses_1"}
    assert len(calls) == 1
    args, kwargs = calls[0]
    assert args == (["opencode", "export", "ses_1"],)
    assert kwargs["text"] is True
    assert kwargs["stderr"] == subprocess.PIPE
    assert kwargs["check"] is False
    assert stdout_was_writable


def test_fetch_export_exits_with_nonzero_status_and_prints_stderr(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    def fake_run(*args, **kwargs):
        return subprocess.CompletedProcess(args[0], 17, stderr="missing session\n")

    monkeypatch.setattr(subprocess, "run", fake_run)

    with pytest.raises(SystemExit) as exc:
        fetch_export("missing")

    assert exc.value.code == 17
    assert capsys.readouterr().err == "missing session\n"


def test_emit_agent_output_writes_chunks_when_output_exceeds_bash_limit(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setenv("BASH_MAX_OUTPUT_LENGTH", "10")
    monkeypatch.setenv("CLAUDE_CODE_FILE_READ_MAX_OUTPUT_TOKENS", "5")
    monkeypatch.chdir(tmp_path)

    output = "line1\nline2\nline3\nline4"
    session_id = "ses_" + uuid.uuid4().hex
    prefix = session_id[:8]

    emit_agent_output(output, session_id)


    rendered = capsys.readouterr().out
    assert "Rendered" in rendered
    chunk_paths = [Path(line.split()[0]) for line in rendered.splitlines() if line.startswith("  /tmp/")]
    assert len(chunk_paths) >= 2
    chunk_dir = chunk_paths[0].parent
    assert chunk_dir.parent == Path("/tmp")
    assert chunk_dir.name.startswith(f"opencode-pretty-{prefix}-")
    assert [path.name for path in chunk_paths] == [f"chunk-{idx}.txt" for idx in range(1, len(chunk_paths) + 1)]
    assert all(path.parent == chunk_dir for path in chunk_paths)
    assert "line1" in chunk_paths[0].read_text()

    shutil.rmtree(chunk_dir)


def test_render_export_emits_drill_down_hint_under_truncated_output() -> None:
    export = sample_export()
    tool_state = export["messages"][1]["parts"][3]["state"]
    tool_state["output"] = "y" * 200
    part_id = export["messages"][1]["parts"][3]["id"]
    session_id = export["info"]["id"]

    rendered = render_export(
        export,
        RenderOptions(no_color=True, tool_max=20),
    )

    expected = (
        f"agent-tools opencode-pretty {session_id} --message {part_id} --full"
    )
    assert expected in rendered


def test_render_export_does_not_emit_hint_when_nothing_truncated() -> None:
    export = sample_export()
    tool_state = export["messages"][1]["parts"][3]["state"]
    tool_state["output"] = "short output"

    rendered = render_export(
        export,
        RenderOptions(no_color=True, tool_max=4000),
    )

    assert "--message" not in rendered


def test_render_export_message_full_mode_returns_only_one_message_untruncated() -> None:
    export = sample_export()
    tool_state = export["messages"][1]["parts"][3]["state"]
    tool_state["output"] = "y" * 2000
    part_id = export["messages"][1]["parts"][3]["id"]

    rendered = render_export(
        export,
        RenderOptions(no_color=True, message_id=part_id, full=True),
    )

    # The full untruncated output appears.
    assert "y" * 2000 in rendered
    # The user message ("please inspect this") is NOT included — only the
    # requested message is rendered.
    assert "please inspect this" not in rendered


def test_render_export_emits_drill_down_hint_under_truncated_error() -> None:
    export = sample_export()
    tool_state = export["messages"][1]["parts"][3]["state"]
    tool_state["status"] = "error"
    tool_state["error"] = "z" * 200
    # Make sure no output is also present so we exercise the error branch.
    tool_state.pop("output", None)
    part_id = export["messages"][1]["parts"][3]["id"]
    session_id = export["info"]["id"]

    rendered = render_export(
        export,
        RenderOptions(no_color=True, tool_max=20),
    )

    expected = (
        f"agent-tools opencode-pretty {session_id} --message {part_id} --full"
    )
    assert expected in rendered
    assert "tool error truncated" in rendered


def test_render_export_emits_drill_down_hint_under_truncated_input() -> None:
    export = sample_export()
    tool_state = export["messages"][1]["parts"][3]["state"]
    tool_state["input"] = {"prompt": "w" * 200}
    part_id = export["messages"][1]["parts"][3]["id"]
    session_id = export["info"]["id"]

    rendered = render_export(
        export,
        RenderOptions(no_color=True, tool_max=20, truncate_input=True),
    )

    expected = (
        f"agent-tools opencode-pretty {session_id} --message {part_id} --full"
    )
    assert expected in rendered
