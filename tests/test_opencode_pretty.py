from __future__ import annotations

import argparse
import io
import json
import subprocess
import sys
from contextlib import redirect_stdout

import pytest

from claude_config.cc_pretty.main import (
    PipelineInput,
    add_shared_args,
    run_pipeline,
)
from claude_config.opencode_pretty.convert import export_to_records
from claude_config.opencode_pretty.main import (
    fetch_export,
    parse_export_stdout,
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
                    "id": "msg_001_user",
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
                    "id": "msg_002_asst",
                    "parentID": "msg_001_user",
                    "time": {"created": 1_700_000_001_456},
                    "providerID": "anthropic",
                    "modelID": "claude-sonnet-4",
                    "tokens": {
                        "input": 10,
                        "output": 20,
                        "reasoning": 0,
                        "cache": {"read": 5, "write": 0},
                    },
                    "finish": "tool_calls",
                },
                "parts": [
                    {"type": "step-start"},
                    {"type": "reasoning", "text": "I should inspect the file first."},
                    {"type": "text", "text": "I will inspect it."},
                    {
                        "type": "tool",
                        "tool": "read",
                        "id": "prt_part_123",
                        "callID": "call_abc",
                        "state": {
                            "status": "completed",
                            "title": "Read /tmp/example.txt",
                            "input": {"filePath": "/tmp/example.txt"},
                            "output": "file contents here",
                            "time": {
                                "start": 1_700_000_001_000,
                                "end": 1_700_000_001_250,
                            },
                        },
                    },
                    {"type": "step-finish"},
                    {"type": "unknown", "text": "ignore me"},
                ],
            },
        ],
    }


def make_args(**overrides) -> argparse.Namespace:
    """Build a fully populated args Namespace for the shared pipeline.

    Front-ends always go through ``add_shared_args``; tests do the same so
    new flags surface as test failures rather than AttributeErrors.
    """
    parser = argparse.ArgumentParser()
    add_shared_args(parser, default_tool_max=4000)
    args = parser.parse_args([])
    for key, value in overrides.items():
        setattr(args, key, value)
    return args


def render(export: dict, **arg_overrides) -> str:
    """Run the full pipeline against ``export`` and return the captured stdout."""
    records, meta = export_to_records(export)
    args = make_args(no_color=True, **arg_overrides)
    buf = io.StringIO()
    with redirect_stdout(buf):
        run_pipeline(PipelineInput(
            records=records,
            log_path=f"opencode://{meta['session_id']}",
            args=args,
            agent_chunk_prefix="opencode-pretty-test",
            rewound=meta.get("rewound_indices") or set(),
        ))
    return buf.getvalue()


# ─── parse_export_stdout ────────────────────────────────────────────────────


def test_parse_export_stdout_skips_status_prefix_before_json() -> None:
    parsed = parse_export_stdout('opencode export\nloading session...\n{"id":"ses_1"}')
    assert parsed == {"id": "ses_1"}


def test_parse_export_stdout_raises_when_no_json_object_exists() -> None:
    with pytest.raises(ValueError, match="no JSON object"):
        parse_export_stdout("opencode export\nloading session...")


def test_parse_export_stdout_raises_for_truncated_json() -> None:
    truncated = 'status prefix\n{"info":{"id":"ses_1"},"messages":[{"info":{"role":"user"}}'
    with pytest.raises(ValueError, match="invalid JSON"):
        parse_export_stdout(truncated)


# ─── fetch_export ────────────────────────────────────────────────────────────


def test_fetch_export_runs_opencode_and_returns_parsed_json(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured = []

    def fake_run(*args, **kwargs):
        captured.append((args, kwargs))
        stdout = kwargs["stdout"]
        stdout.write('{"id":"ses_1"}')
        stdout.flush()
        return subprocess.CompletedProcess(args[0], 0, stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)
    assert fetch_export("ses_1") == {"id": "ses_1"}
    (args, kwargs), = captured
    assert args == (["opencode", "export", "ses_1"],)
    assert kwargs["stderr"] == subprocess.PIPE
    assert kwargs["check"] is False


def test_fetch_export_propagates_nonzero_exit_and_stderr(
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


# ─── export_to_records ──────────────────────────────────────────────────────


def test_export_to_records_emits_user_assistant_and_tool_result_records() -> None:
    records, meta = export_to_records(sample_export())
    # 1 user + 1 assistant + 1 synthetic tool-result UserRecord = 3 records.
    assert len(records) == 3
    assert meta["session_id"] == "ses_1234567890abcdef"
    assert meta["title"] == "Parser work"
    assert meta["model"] == "openai/gpt-5.5/xhigh"
    assert meta["rewound_indices"] == set()


def test_export_to_records_drops_synthetic_step_markers() -> None:
    output = render(sample_export(), no_thinking=True, truncate_input=True)
    assert "step-start" not in output
    assert "step-finish" not in output


def test_render_pipeline_shows_session_header_and_model_label() -> None:
    output = render(sample_export(), no_thinking=True)
    assert "ses_1234" in output
    assert "parser-work" in output
    assert "1.15.5+0086a0b" in output
    assert "/root/claude-config-work2" in output
    # The assistant turn header tags the model that produced THAT turn,
    # not the session default — assistant has providerID/modelID directly.
    assert "anthropic/claude-sonnet-4" in output


def test_render_pipeline_renders_reasoning_text_and_tool_call() -> None:
    output = render(sample_export(), tool_max=1000, truncate_input=True)
    assert "I should inspect the file first." in output
    assert "I will inspect it." in output
    assert "▶ read" in output
    assert "filePath: /tmp/example.txt" in output
    assert "◀ result" in output
    assert "file contents here" in output


def test_render_pipeline_collapses_thinking_under_no_thinking() -> None:
    output = render(sample_export(), no_thinking=True, tool_max=1000, truncate_input=True)
    assert "[thinking:" in output
    assert "I should inspect the file first." not in output


def test_render_pipeline_error_tool_state_surfaces_error_text() -> None:
    export = sample_export()
    tool_part = export["messages"][1]["parts"][3]
    tool_part["state"] = {
        "status": "error",
        "input": {"filePath": "/tmp/missing.txt"},
        "error": "File not found: /tmp/missing.txt",
    }
    output = render(export, tool_max=1000, truncate_input=True)
    assert "error" in output
    assert "File not found: /tmp/missing.txt" in output


def test_render_pipeline_chat_only_drops_tool_io_but_keeps_text_and_thinking() -> None:
    output = render(sample_export(), chat_only=True, tool_max=1000, truncate_input=True)
    assert "please inspect this" in output
    assert "I will inspect it." in output
    # Tool call line and result line should both be gone under chat-only.
    assert "▶ read" not in output
    assert "◀ result" not in output
    assert "file contents here" not in output


def test_render_pipeline_truncate_input_respects_tool_max() -> None:
    export = sample_export()
    export["messages"][1]["parts"][3]["state"]["input"] = {"prompt": "x" * 200}
    untruncated = render(export, tool_max=20, truncate_input=False)
    truncated = render(export, tool_max=20, truncate_input=True)
    assert "x" * 200 in untruncated
    assert "x" * 200 not in truncated
    assert "more chars" in truncated


# ─── Compaction detection ───────────────────────────────────────────────────


def _add_compaction(export: dict) -> dict:
    """Insert a compaction user msg + summary assistant msg after position 1."""
    msgs = export["messages"]
    ses_id = export["info"]["id"]
    compact_user = {
        "info": {
            "role": "user",
            "id": "msg_003_compactuser",  # > both msg_001_user and msg_002_asst
            "sessionID": ses_id,
            "agent": "compaction",
            "model": {"providerID": "openai", "modelID": "gpt-5.5"},
            "time": {"created": 1_700_000_002_000},
        },
        "parts": [{
            "id": "prt_compact",
            "type": "compaction",
            "auto": False,
            "overflow": False,
        }],
    }
    compact_asst = {
        "info": {
            "role": "assistant",
            "id": "msg_004_compactasst",
            "parentID": "msg_003_compactuser",
            "sessionID": ses_id,
            "summary": True,
            "modelID": "gpt-5.5",
            "providerID": "openai",
            "tokens": {"input": 50, "output": 5, "reasoning": 0,
                       "cache": {"read": 0, "write": 0}},
            "time": {"created": 1_700_000_002_500},
        },
        "parts": [{"type": "text", "text": "## Goal\n- Test compaction"}],
    }
    follow_user = {
        "info": {
            "role": "user",
            "id": "msg_005_follow",
            "sessionID": ses_id,
            "time": {"created": 1_700_000_003_000},
        },
        "parts": [{"type": "text", "text": "post-compact prompt"}],
    }
    export = {**export, "messages": msgs + [compact_user, compact_asst, follow_user]}
    return export


def test_compaction_marker_appears_at_compaction_boundary() -> None:
    output = render(_add_compaction(sample_export()))
    assert "⟐ compacted" in output
    assert "section 1" in output


def test_compaction_default_hides_pre_compact_leg() -> None:
    output = render(_add_compaction(sample_export()))
    # The first user prompt sits in the pre-compact leg and should be hidden.
    assert "please inspect this" not in output
    # Post-compact content is visible.
    assert "post-compact prompt" in output


def test_compaction_all_shows_every_leg() -> None:
    output = render(_add_compaction(sample_export()), compact_all=True)
    assert "please inspect this" in output
    assert "post-compact prompt" in output


def test_compaction_leg_zero_shows_only_pre_compact_section() -> None:
    output = render(_add_compaction(sample_export()), compact_leg=0)
    assert "please inspect this" in output
    assert "post-compact prompt" not in output


# ─── Rewind / revert ────────────────────────────────────────────────────────


def test_revert_with_no_part_id_marks_target_and_after_as_rewound() -> None:
    export = sample_export()
    # Revert to msg_001_user (no partID). msg_001_user and everything after are
    # rewound; nothing remains because msg_001_user is the very first message.
    export["info"]["revert"] = {"messageID": "msg_001_user"}
    output = render(export)
    assert "⟲ rewind" in output
    assert "please inspect this" not in output


def test_revert_with_part_id_keeps_target_message_visible() -> None:
    export = sample_export()
    # With partID, the boundary message itself stays — only later messages
    # are rewound. msg_002_asst > msg_001_user so it's rewound; user stays.
    export["info"]["revert"] = {
        "messageID": "msg_001_user",
        "partID": "prt_any",
    }
    output = render(export)
    assert "⟲ rewind" in output
    assert "please inspect this" in output
    assert "I will inspect it." not in output


def test_no_revert_state_produces_no_rewind_marker() -> None:
    output = render(sample_export())
    assert "⟲ rewind" not in output


def test_show_rewound_displays_rewound_records() -> None:
    export = sample_export()
    export["info"]["revert"] = {"messageID": "msg_002_asst", "partID": "prt_x"}
    # msg_002_asst == cutoff (kept under partID semantics), so nothing is
    # actually rewound — flip the cutoff one earlier and test the visible path.
    export["info"]["revert"] = {"messageID": "msg_001_user"}
    output = render(export, show_rewound=True)
    assert "⟲ rewind" in output
    # Under --show-rewound, the rewound content is included.
    assert "please inspect this" in output


# ─── Source-true part indices (_pi / _out_len) ──────────────────────────────


def test_export_to_records_tags_blocks_with_source_part_index() -> None:
    records, _ = export_to_records(sample_export())
    asst = records[1][0]
    blocks = asst.message.content_blocks()
    # parts: [step-start(0), reasoning(1), text(2), tool(3), step-finish(4),
    #         unknown(5)] — rendered blocks must keep the export's indices.
    assert getattr(blocks[0], "_pi") == 1  # thinking (reasoning part)
    assert getattr(blocks[1], "_pi") == 2  # text part
    assert getattr(blocks[2], "_pi") == 3  # tool_use part
    assert getattr(blocks[2], "_out_len") == len("file contents here")
    result_blocks = records[2][0].message.content_blocks()
    assert getattr(result_blocks[0], "_pi") == 3  # result refs the tool part


def test_export_to_records_tags_user_record_with_first_text_part_index() -> None:
    records, _ = export_to_records(sample_export())
    user_rec = records[0][0]
    assert getattr(user_rec, "_pi") == 0  # sole text part at index 0


# ─── Legend ─────────────────────────────────────────────────────────────────


def test_legend_emits_opencode_recovery_hint_for_opencode_log_path() -> None:
    output = render(sample_export())
    assert "opencode export ses_1234567890abcdef" in output
    assert "jq" in output
    # The Claude-Code-specific recovery wording must not leak through.
    assert "sed -n" not in output


# ─── Color auto-detection ────────────────────────────────────────────────────

# Unit coverage for the color decision lives in test_cc_pretty_render.py
# (detect_color is shared via cc_pretty.main). Here we only check the CLI
# end-to-end. These run in a subprocess: a clean interpreter avoids the
# global C.disable() that test_cc_pretty_render applies at import time, and
# captured stdout is a pipe, exercising the real auto-detection path.

def _run_cli(export_file, *flags: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable, "-m", "claude_config.opencode_pretty.main",
            "ses_test", "--from-file", str(export_file), *flags,
        ],
        capture_output=True,
        text=True,
        check=False,
    )


def test_cli_disables_color_when_stdout_is_piped(tmp_path) -> None:
    export_file = tmp_path / "export.json"
    export_file.write_text(json.dumps(sample_export()))
    proc = _run_cli(export_file)
    assert proc.returncode == 0
    assert "\033[" not in proc.stdout


def test_cli_color_flag_forces_ansi_when_piped(tmp_path) -> None:
    export_file = tmp_path / "export.json"
    export_file.write_text(json.dumps(sample_export()))
    proc = _run_cli(export_file, "--color")
    assert proc.returncode == 0
    assert "\033[" in proc.stdout


def test_cli_rejects_color_and_no_color_together(tmp_path) -> None:
    export_file = tmp_path / "export.json"
    export_file.write_text(json.dumps(sample_export()))
    proc = _run_cli(export_file, "--color", "--no-color")
    assert proc.returncode == 2
    assert "not allowed with argument" in proc.stderr
