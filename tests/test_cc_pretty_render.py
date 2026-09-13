from __future__ import annotations

import argparse
import io
import json
import subprocess
import sys

import pytest

from claude_config.cc_pretty.main import add_shared_args, detect_color
from claude_config.cc_pretty.parse import (
    AssistantRecord,
    AttachmentData,
    AttachmentRecord,
    Message,
    ToolResultBlock,
    Usage,
    UserRecord,
)
from claude_config.cc_pretty.render import (
    C,
    Renderer,
    block_ref,
    fmt_ref,
    legend_lines,
    recovery_cmd,
    render_legend,
    separator,
    trunc,
)

C.disable()  # All tests assert on plain text — no ANSI escapes.


def test_trunc_short_string_returns_unchanged() -> None:
    assert trunc("hello", 100) == "hello"


def test_trunc_long_string_without_next_step_uses_head_tail() -> None:
    s = "A" * 500 + "B" * 500 + "C" * 500
    out = trunc(s, 90)
    # Head 60 chars + omission + tail 30 chars (approx — exact split is
    # 2/3 head, 1/3 tail; the assertions below check the structure only).
    assert out.startswith("A")
    assert out.endswith("C" * 30)  # tail = maxlen - head = 90 - 60 = 30
    assert "more chars" in out
    assert "NEXT STEP" not in out  # control: no NEXT STEP in input


def test_trunc_preserves_next_step_in_mid_text() -> None:
    body = "X" * 2000
    needle = "NEXT STEP: run step 2 now"
    s = body + needle + body
    out = trunc(s, 200)
    assert needle in out
    # Window around NEXT STEP should preserve some surrounding context.
    needle_idx = out.index(needle)
    assert needle_idx > 0
    assert out[needle_idx - 10 : needle_idx] == "X" * 10


def test_trunc_extends_head_when_next_step_overlaps_head_window() -> None:
    # NEXT STEP is inside what would normally be the head window.
    needle = "NEXT STEP do thing"
    s = "Y" * 30 + needle + "Y" * 5000
    out = trunc(s, 200)
    assert needle in out
    # No isolated NEXT STEP window — head already covers it.
    # The output should contain exactly one "more chars" gap (the tail gap
    # gone, the mid gap not created).
    assert out.count("more chars") == 1


def test_trunc_extends_tail_when_next_step_overlaps_tail_window() -> None:
    needle = "NEXT STEP finish up"
    s = "Z" * 5000 + needle + "Z" * 30
    out = trunc(s, 200)
    assert needle in out
    assert out.count("more chars") == 1


def test_trunc_merges_close_next_step_windows() -> None:
    needle1 = "NEXT STEP one"
    needle2 = "NEXT STEP two"
    s = "P" * 3000 + needle1 + "Q" * 50 + needle2 + "P" * 3000
    out = trunc(s, 200)
    assert needle1 in out
    assert needle2 in out
    # Two close windows merge into one — between needle1 and needle2 the
    # text is preserved (no omission between them).
    span = out[out.index(needle1) : out.index(needle2) + len(needle2)]
    assert "more chars" not in span


def test_trunc_keeps_separate_windows_for_far_apart_next_steps() -> None:
    needle1 = "NEXT STEP first"
    needle2 = "NEXT STEP second"
    s = "R" * 3000 + needle1 + "S" * 5000 + needle2 + "R" * 3000
    out = trunc(s, 200)
    assert needle1 in out
    assert needle2 in out
    # Far-apart windows leave an omission gap between them.
    span = out[out.index(needle1) : out.index(needle2)]
    assert "more chars" in span


# ─── fmt_ref / legend / separator (token-efficient back-references) ────────


def test_fmt_ref_omits_block_index_when_zero() -> None:
    # Single-block records are the common case; the bracket is noise.
    assert fmt_ref(42) == "@L42"
    assert fmt_ref(42, 0) == "@L42"


def test_fmt_ref_includes_block_index_when_nonzero() -> None:
    assert fmt_ref(42, 2) == "@L42[2]"


def test_render_legend_contains_recovery_recipe() -> None:
    out = render_legend("/path/to/sess.jsonl")
    assert "@L<n>" in out
    assert "sed -n" in out
    assert "/path/to/sess.jsonl" in out
    # Lists all four jq-paths a reader might need.
    assert ".input" in out
    assert ".content" in out
    assert ".text" in out
    assert ".attachment.content" in out


def test_separator_is_form_feed() -> None:
    # Form feed = 1 token under cl100k_base; renders as a horizontal rule in
    # Emacs page-break-lines-mode. The function returns a single FF char.
    assert separator() == "\f"


# ─── output_style dedup (renderer-state behavior) ──────────────────────────


def _output_style_record(style: str) -> AttachmentRecord:
    return AttachmentRecord(
        type="attachment",
        attachment=AttachmentData(type="output_style", style=style),
    )


def test_output_style_dedup_emits_first_and_changes_only() -> None:
    r = Renderer("/tmp/log.jsonl", tool_output_max=200, tool_input_max=200)
    a = _output_style_record("alan-default-next")
    b = _output_style_record("alan-default-next")  # same → suppressed
    c = _output_style_record("other-style")        # new → emitted
    d = _output_style_record("other-style")        # same → suppressed

    first = r.render_attachment(a, ts="00:00:00", lineno=1)
    second = r.render_attachment(b, ts="00:00:01", lineno=2)
    third = r.render_attachment(c, ts="00:00:02", lineno=3)
    fourth = r.render_attachment(d, ts="00:00:03", lineno=4)

    assert first is not None and "alan-default-next" in first
    assert second is None
    assert third is not None and "other-style" in third
    assert fourth is None


# ─── tool_use / tool_result rendering (no toolu IDs, ref in head) ──────────


# ─── render_assistant_turn: usage-by-flag, no stop tag ─────────────────────


def _assistant_record(
    model: str = "claude-opus-4-7",
    stop_reason: str | None = "tool_use",
    usage: Usage | None = None,
) -> AssistantRecord:
    return AssistantRecord(
        type="assistant",
        message=Message(
            role="assistant",
            model=model,
            stop_reason=stop_reason,
            usage=usage,
            content=[],
        ),
    )


def test_assistant_header_hides_usage_by_default() -> None:
    u = Usage(input_tokens=6, output_tokens=128, cache_read_input_tokens=12914,
              cache_creation_input_tokens=17450)
    r = Renderer("/tmp/log.jsonl", tool_output_max=200, tool_input_max=200)
    out = r.render_assistant_turn([(_assistant_record(usage=u), 1)], ts="00:00:00")
    head = out.splitlines()[0]
    assert "in:6" not in head
    assert "out:128" not in head
    assert "cached" not in head
    assert "[claude-opus-4-7]" in head


def test_assistant_header_shows_usage_when_flagged() -> None:
    u = Usage(input_tokens=6, output_tokens=128, cache_read_input_tokens=12914,
              cache_creation_input_tokens=17450)
    r = Renderer("/tmp/log.jsonl", tool_output_max=200, tool_input_max=200,
                 show_usage=True)
    out = r.render_assistant_turn([(_assistant_record(usage=u), 1)], ts="00:00:00")
    head = out.splitlines()[0]
    assert "in:6" in head
    assert "out:128" in head
    assert "cached:12,914" in head


def test_assistant_header_drops_stop_reason() -> None:
    r = Renderer("/tmp/log.jsonl", tool_output_max=200, tool_input_max=200)
    # All stop reasons are suppressed — tool_use is implied by the next ▶
    # line, others (refusal, max_tokens, pause_turn) surface in the body.
    for reason in ("tool_use", "refusal", "max_tokens", "pause_turn", "end_turn"):
        out = r.render_assistant_turn(
            [(_assistant_record(stop_reason=reason), 1)], ts="00:00:00",
        )
        head = out.splitlines()[0]
        assert "stop:" not in head, f"stop:{reason} leaked into: {head!r}"


def test_render_tool_use_has_ref_and_no_toolu_id() -> None:
    from claude_config.cc_pretty.parse import ToolUseBlock

    r = Renderer("/tmp/log.jsonl", tool_output_max=200, tool_input_max=200)
    block = ToolUseBlock(
        type="tool_use",
        id="toolu_01ABCDEFGHIJKLMNOPQRSTUV",
        name="Bash",
        input={"command": "ls"},
    )
    out = r._render_tool_use(block, lineno=17, block_idx=0)
    assert "▶ Bash" in out
    assert "@L17" in out
    # ID is intentionally omitted — correlation comes from line numbers
    # and the tool name printed on the result line.
    assert "toolu_" not in out
    # No jq_hint trailer (the legend documents the recipe once).
    assert "sed -n" not in out


# ─── Color auto-detection ────────────────────────────────────────────────────

# detect_color lives in cc_pretty.main and is applied centrally in
# run_pipeline, so cc-pretty and opencode-pretty share the behavior; the
# unit tests here cover the decision, with one CLI end-to-end pair below.


class _FakeTty(io.StringIO):
    def isatty(self) -> bool:
        return True


def _args(**overrides) -> argparse.Namespace:
    """Build a fully populated args Namespace via the shared CLI surface."""
    parser = argparse.ArgumentParser()
    add_shared_args(parser, default_tool_max=200)
    args = parser.parse_args([])
    for key, value in overrides.items():
        setattr(args, key, value)
    return args


def test_detect_color_no_color_flag_always_wins(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "stdout", _FakeTty())
    monkeypatch.delenv("NO_COLOR", raising=False)
    assert detect_color(_args(no_color=True, color=True)) is False


def test_detect_color_color_flag_forces_on_when_piped(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "stdout", io.StringIO())  # not a TTY
    monkeypatch.setenv("NO_COLOR", "1")  # explicit flag also overrides the env var
    assert detect_color(_args(color=True)) is True


def test_detect_color_no_color_env_disables_on_tty(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "stdout", _FakeTty())
    monkeypatch.setenv("NO_COLOR", "1")
    assert detect_color(_args()) is False


def test_detect_color_empty_no_color_env_is_ignored(monkeypatch: pytest.MonkeyPatch) -> None:
    # no-color.org: only a present *and non-empty* NO_COLOR disables color.
    monkeypatch.setattr(sys, "stdout", _FakeTty())
    monkeypatch.setenv("NO_COLOR", "")
    assert detect_color(_args()) is True


def test_detect_color_off_when_stdout_is_not_a_tty(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "stdout", io.StringIO())
    monkeypatch.delenv("NO_COLOR", raising=False)
    assert detect_color(_args()) is False


def test_detect_color_on_for_tty_without_no_color_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "stdout", _FakeTty())
    monkeypatch.delenv("NO_COLOR", raising=False)
    assert detect_color(_args()) is True


# End-to-end CLI tests run in a subprocess: a clean interpreter avoids the
# module-level C.disable() above, and captured stdout is a pipe, exercising
# the real auto-detection path.

def _run_cli(jsonl_file, *flags: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "claude_config.cc_pretty.main", str(jsonl_file), *flags],
        capture_output=True,
        text=True,
        check=False,
    )


def _write_jsonl(tmp_path):
    jsonl = tmp_path / "session.jsonl"
    record = {"type": "user", "message": {"role": "user", "content": "hi"}}
    jsonl.write_text(json.dumps(record) + "\n")
    return jsonl


def test_cli_disables_color_when_stdout_is_piped(tmp_path) -> None:
    proc = _run_cli(_write_jsonl(tmp_path))
    assert proc.returncode == 0
    assert "\033[" not in proc.stdout


def test_cli_color_flag_forces_ansi_when_piped(tmp_path) -> None:
    proc = _run_cli(_write_jsonl(tmp_path), "--color")
    assert proc.returncode == 0
    assert "\033[" in proc.stdout


def test_cli_rejects_color_and_no_color_together(tmp_path) -> None:
    proc = _run_cli(_write_jsonl(tmp_path), "--color", "--no-color")
    assert proc.returncode == 2
    assert "not allowed with argument" in proc.stderr


# ─── block_ref / recovery_cmd / legend_lines (direct-str access) ────────────


def test_block_ref_prefers_source_part_index_when_present() -> None:
    class _B:
        pass
    b = _B()
    b._pi = 3
    assert block_ref(b, 2, 0) == "@L2[3]"
    assert block_ref(_B(), 2, 0) == "@L2"      # no _pi → enumeration index
    assert block_ref(_B(), 2, 1) == "@L2[1]"


def test_recovery_cmd_opencode_session() -> None:
    cmd = recovery_cmd("opencode://ses_abc", 5, 3, ".state.output")
    assert cmd == (
        "opencode export ses_abc > /tmp/oc-ses_abc.json && "
        "jq -r '.messages[4].parts[3].state.output' /tmp/oc-ses_abc.json"
    )


def test_recovery_cmd_opencode_from_file() -> None:
    cmd = recovery_cmd("opencode-file:///tmp/x.json", 5, 3, ".text")
    assert cmd == "jq -r '.messages[4].parts[3].text' /tmp/x.json"


def test_recovery_cmd_cc_block_and_record_level() -> None:
    assert recovery_cmd("/tmp/s.jsonl", 57, 0, ".content") == (
        "sed -n '57p' /tmp/s.jsonl | jq -r '.message.content[0].content'"
    )
    assert recovery_cmd("/tmp/s.jsonl", 12, None, ".message.content") == (
        "sed -n '12p' /tmp/s.jsonl | jq -r '.message.content'"
    )


def test_legend_lines_cover_every_block_type_per_harness() -> None:
    cc = "\n".join(legend_lines("/tmp/s.jsonl"))
    for token in (".thinking", ".text", ".input", ".content",
                  ".message.content", ".attachment.content", "sed -n"):
        assert token in cc, token
    assert "context .text" in cc  # ◀ context blocks are TextBlocks (leaf .text)
    oc = "\n".join(legend_lines("opencode://ses_x"))
    for token in (".text", ".state.input", ".state.output",
                  "opencode export ses_x"):
        assert token in oc, token
    oc_file = "\n".join(legend_lines("opencode-file:///tmp/x.json"))
    assert "opencode export" not in oc_file
    assert "jq -r" in oc_file and "/tmp/x.json" in oc_file


def test_cc_tool_result_truncation_hint_uses_sed_and_content_leaf() -> None:
    r = Renderer("/tmp/s.jsonl", tool_output_max=50, tool_input_max=50)
    block = ToolResultBlock(
        type="tool_result", tool_use_id="toolu_x", content="z" * 500,
    )
    out = r._render_tool_result(block, lineno=9, block_idx=0)
    assert "…full: sed -n '9p' /tmp/s.jsonl | jq -r '.message.content[0].content'" in out


# ─── MCP array-shaped toolUseResult ────────────────────────────────────────
# MCP tools store their raw content-block array in toolUseResult, and the
# tool_result block carries that same array — so the body appears once.


def _mcp_array_record() -> tuple[UserRecord, int]:
    blocks = [
        {"type": "text", "text": "Navigated to https://example.com"},
        {"type": "text", "text": "<system-reminder>Prefer browser_batch.</system-reminder>"},
    ]
    rec = UserRecord(
        type="user",
        message=Message(
            role="user",
            content=[{
                "type": "tool_result",
                "tool_use_id": "toolu_mcp1",
                "content": blocks,
            }],
        ),
        toolUseResult=blocks,
    )
    return rec, 12


def test_parse_tool_use_result_accepts_mcp_content_block_array() -> None:
    rec, _ = _mcp_array_record()
    assert rec.parsed_tool_use_result() == [
        {"type": "text", "text": "Navigated to https://example.com"},
        {"type": "text", "text": "<system-reminder>Prefer browser_batch.</system-reminder>"},
    ]


def test_tool_output_renders_mcp_array_result_body_once() -> None:
    r = Renderer("/tmp/s.jsonl", tool_output_max=500, tool_input_max=500)
    out = r.render_tool_output([_mcp_array_record()], ts="00:00:00")
    assert out.count("Navigated to https://example.com") == 1
    assert out.count("Prefer browser_batch") == 1


def test_cli_renders_session_with_mcp_array_tool_use_result(tmp_path) -> None:
    blocks = [{"type": "text", "text": "Navigated to https://example.com"}]
    jsonl = tmp_path / "mcp.jsonl"
    jsonl.write_text(json.dumps({
        "type": "user",
        "message": {"role": "user", "content": [
            {"type": "tool_result", "tool_use_id": "toolu_mcp1", "content": blocks},
        ]},
        "toolUseResult": blocks,
    }) + "\n")
    proc = _run_cli(jsonl)
    assert proc.returncode == 0, proc.stderr
    assert "Navigated to https://example.com" in proc.stdout


def test_tool_output_omits_mcp_array_result_that_diverges_from_body() -> None:
    # An oversized MCP result is the one shape where toolUseResult holds more
    # than the tool_result block. The block states the elision and names the
    # file, so the array stays unrendered — see
    # notes/mcp-tool-use-result-array.md.
    rec = UserRecord(
        type="user",
        message=Message(
            role="user",
            content=[{
                "type": "tool_result",
                "tool_use_id": "toolu_big",
                "content": "Output too large (60013 chars). "
                           "Full output saved to: /tmp/mcp-out.txt",
            }],
        ),
        toolUseResult=[{"type": "text", "text": "SPILLED-BODY-" + "x" * 60000}],
    )
    r = Renderer("/tmp/s.jsonl", tool_output_max=500, tool_input_max=500)
    out = r.render_tool_output([(rec, 3)], ts="00:00:00")
    assert "SPILLED-BODY" not in out
    assert "Full output saved to: /tmp/mcp-out.txt" in out


# The plugin-eval tools JSON.parse arbitrary output into toolUseResult, so
# every JSON value is legal there. Only the object form is modelled.
@pytest.mark.parametrize("value", [42, 0, -1.5, True, False, "text", [],
                                   ["a", 1], [{"type": "text", "text": "x"}],
                                   None])
def test_parse_tool_use_result_returns_non_object_json_unchanged(value) -> None:
    rec = UserRecord(type="user", message=Message(role="user", content=[]),
                     toolUseResult=value)
    assert rec.parsed_tool_use_result() == value


def test_parse_tool_use_result_models_the_object_form() -> None:
    rec = UserRecord(type="user", message=Message(role="user", content=[]),
                     toolUseResult={"stdout": "out", "stderr": "err"})
    assert rec.parsed_tool_use_result().stderr == "err"


def test_cli_renders_session_with_scalar_tool_use_result(tmp_path) -> None:
    jsonl = tmp_path / "scalar.jsonl"
    jsonl.write_text(json.dumps({
        "type": "user",
        "message": {"role": "user", "content": [
            {"type": "tool_result", "tool_use_id": "toolu_s", "content": "42"},
        ]},
        "toolUseResult": 42,
    }) + "\n")
    proc = _run_cli(jsonl)
    assert proc.returncode == 0, proc.stderr


def _rendered_record(atype: str, content: str) -> AttachmentRecord:
    return AttachmentRecord(
        type="attachment",
        attachment=AttachmentData(type=atype),
        rendered=[{"content": content}],
    )


def test_a_subtype_with_no_arm_prints_what_it_sent_the_model() -> None:
    # Claude Code delivers most of its context as attachments whose subtype
    # this renderer has never heard of -- the environment block among them.
    # Naming the record while dropping its text is the failure that matters.
    r = Renderer("/tmp/log.jsonl", tool_output_max=200, tool_input_max=200)
    out = r.render_attachment(
        _rendered_record(
            "environment",
            "<system-reminder>\n# Environment\nPrimary working directory: /x\n</system-reminder>",
        ),
        ts="00:00:00",
        lineno=4,
    )
    assert out is not None
    assert "environment" in out
    assert "Primary working directory: /x" in out
    # The wrapper is scaffolding every one of them carries; the text is not.
    assert "<system-reminder>" not in out


def test_an_overlong_attachment_preview_carries_its_recovery_path() -> None:
    r = Renderer("/tmp/log.jsonl", tool_output_max=200, tool_input_max=200)
    body = "x" * (r.tool_output_max + 500)
    out = r.render_attachment(
        _rendered_record("session_context", body), ts="00:00:00", lineno=9
    )
    assert out is not None
    assert len(out.splitlines()[0]) < len(body)
    # jq path must name where the text actually lives, or the hint is a dead end.
    assert ".rendered[].content" in out
    assert "sed -n '9p'" in out


def test_an_attachment_carrying_no_rendered_text_still_names_itself() -> None:
    r = Renderer("/tmp/log.jsonl", tool_output_max=200, tool_input_max=200)
    rec = AttachmentRecord(type="attachment", attachment=AttachmentData(type="mystery"))
    out = r.render_attachment(rec, ts="00:00:00", lineno=1)
    assert out is not None
    assert "mystery" in out


# ── Skeleton: an attachment whose payload lives in `rendered` gets a row ─────


def _skeleton(*records: object) -> str:
    from claude_config.cc_pretty.render import render_skeleton

    return render_skeleton(
        [(rec, i + 1) for i, rec in enumerate(records)],
        log_path="/tmp/x.jsonl",
        compact_hidden=set(),
        hidden_for_rewind=set(),
        compaction_markers={},
        rewind_markers={},
        record_visible=lambda _rec: True,
    )


def test_skeleton_rows_an_attachment_whose_payload_is_in_rendered() -> None:
    """2.1.269 delivers most context with `.attachment.content` empty.

    The default view was taught to read `rendered`; the skeleton was not, and
    it `continue`d on empty content -- emitting no row at all. That breaks the
    one promise the skeleton makes (`skills/session-analysis/SKILL.md`: one
    line per content block), and it breaks it silently, in the substrate a
    reader uses to decide what to extract.
    """
    out = _skeleton(
        _rendered_record(
            "environment",
            "<system-reminder>\n# Environment\nPrimary working directory: /x\n</system-reminder>",
        )
    )
    assert "attach:environment" in out
    row = next(line for line in out.splitlines() if "attach:environment" in line)
    # The jq leaf must name where the text actually is, or extraction from the
    # skeleton lands on the empty field.
    assert ".rendered[].content" in row
    assert "Primary working directory: /x" in row
    # Scaffolding every one of them carries; it would crowd out the 50 chars
    # that distinguish one row from the next.
    assert "<system-reminder>" not in row


def test_skeleton_prefers_attachment_content_when_it_is_populated() -> None:
    rec = AttachmentRecord(
        type="attachment",
        attachment=AttachmentData(type="diagnostics", content="real payload here"),
        rendered=[{"content": "conversion output"}],
    )
    row = next(
        line for line in _skeleton(rec).splitlines() if "attach:diagnostics" in line
    )
    assert ".attachment.content" in row
    assert "real payload here" in row


def test_skeleton_still_omits_an_attachment_with_no_payload_anywhere() -> None:
    rec = AttachmentRecord(type="attachment", attachment=AttachmentData(type="mystery"))
    assert "attach:mystery" not in _skeleton(rec)
