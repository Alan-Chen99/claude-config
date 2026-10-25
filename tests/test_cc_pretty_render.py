from __future__ import annotations

import argparse
import base64
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
    SystemRecord,
    ToolResultBlock,
    Usage,
    UserRecord,
    parse_record,
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
    """2.1.269 delivers most context with `.attachment.content` empty and the
    text in `rendered`; a skeleton that reads only the former emits no row,
    breaking its one promise (`skills/session-analysis/SKILL.md`: one line per
    content block).
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


# ─── A message the user typed while the agent was running ────────────────────
# It never becomes a `user` record. Claude Code queues it, logs the wait as
# `queue-operation`, and delivers it as a `queued_command` attachment whose text
# is at `.attachment.prompt` — a field neither of the other two payload leaves
# reaches. The lifecycle below is the one real logs carry.


def _queue_session(tmp_path) -> object:
    """A session carrying each shape a queued message reaches cc-pretty in."""
    jsonl = tmp_path / "queued.jsonl"
    records = [
        {"type": "user", "uuid": "u0", "message": {"role": "user", "content": "start"}},
        {"type": "assistant", "uuid": "a0", "message": {
            "role": "assistant", "model": "claude-opus-5", "content": [
                {"type": "tool_use", "id": "toolu_1", "name": "Bash",
                 "input": {"command": "sleep 60"}}]}},
        {"type": "user", "uuid": "u1", "message": {"role": "user", "content": [
            {"type": "tool_result", "tool_use_id": "toolu_1", "content": "done"}]}},
        # Typed mid-run, then popped back into the editor to reword: enqueued,
        # never delivered, and carried by no other record in the log.
        {"type": "queue-operation", "operation": "enqueue",
         "content": "wait, use the other flag"},
        {"type": "queue-operation", "operation": "popAll",
         "content": "wait, use the other flag"},
        # The reworded one, delivered. `remove` ends its wait and restates it.
        {"type": "queue-operation", "operation": "enqueue",
         "content": "wait, use --porcelain instead"},
        {"type": "queue-operation", "operation": "remove",
         "content": "wait, use --porcelain instead"},
        {"type": "attachment", "uuid": "q0", "attachment": {
            "type": "queued_command", "commandMode": "prompt",
            "prompt": "wait, use --porcelain instead"}},
        # Same delivery, 2.1.269 shape: `rendered` holds the prompt under cc's
        # own framing, which says the same thing on every such record.
        {"type": "attachment", "uuid": "q1", "attachment": {
            "type": "queued_command", "commandMode": "prompt",
            "prompt": "and commit when it passes"},
         "rendered": [{"content":
                       "<system-reminder>\nThe user sent a new message while "
                       "you were working:\nand commit when it passes\n"
                       "</system-reminder>"}]},
        # A pasted image makes `prompt` a block list (chunk-j0tbz6ra.js:204089).
        {"type": "attachment", "uuid": "q2", "attachment": {
            "type": "queued_command", "commandMode": "prompt", "prompt": [
                {"type": "text", "text": "this screenshot shows the bug"},
                {"type": "image", "source": _image_source()}]}},
        # The other mode off the same queue: a background job reporting.
        {"type": "attachment", "uuid": "q3", "attachment": {
            "type": "queued_command", "commandMode": "task-notification",
            "prompt": "<task-notification>\n<status>completed</status>\n"
                      "</task-notification>"}},
        {"type": "assistant", "uuid": "a1", "message": {
            "role": "assistant", "model": "claude-opus-5",
            "content": [{"type": "text", "text": "switching to --porcelain"}]}},
    ]
    jsonl.write_text("\n".join(json.dumps(r) for r in records) + "\n")
    return jsonl


def _row(out: str, needle: str) -> str:
    rows = [line for line in out.splitlines() if needle in line]
    assert len(rows) == 1, f"{needle}: expected one row, got {rows}"
    return rows[0]


def test_the_skeleton_rows_a_message_the_user_typed_mid_run(tmp_path) -> None:
    """The delivered prompt is a user turn, and a skeleton is how a reader finds
    one. Sourced from `.attachment.content` or `rendered` alone it has no
    payload, so it got no row at all — the whole message invisible.
    """
    out = _render(_queue_session(tmp_path), "--skeleton")
    row = _row(out, "wait, use --porcelain instead")
    assert "user:prompt" in row
    # The leaf has to name where the text is, or extraction from the skeleton
    # lands on an empty field.
    assert ".attachment.prompt" in row


def test_a_queued_prompt_previews_the_user_not_the_framing(tmp_path) -> None:
    """`rendered` wraps the prompt in `The user sent a new message while you
    were working:` plus a paragraph — a median 132 tokens, the same on every
    such record. Read from there, every row previews the boilerplate and charges
    it to the size column a reader budgets by.
    """
    row = _row(_render(_queue_session(tmp_path), "--skeleton"),
               "and commit when it passes")
    assert ".attachment.prompt" in row
    assert "The user sent a new message" not in row


def test_a_queued_prompt_carrying_an_image_still_reaches_the_skeleton(tmp_path) -> None:
    """A pasted image makes `prompt` a block list. Typed as a string alone it
    fails validation and parse_all drops the record, user's message included.
    """
    row = _row(_render(_queue_session(tmp_path), "--skeleton"),
               "this screenshot shows the bug")
    assert "user:prompt" in row
    assert ".attachment.prompt[].text" in row


def test_a_task_notification_off_the_queue_is_labelled_by_its_mode(tmp_path) -> None:
    row = _row(_render(_queue_session(tmp_path), "--skeleton"), "task-notification>")
    assert "user:task-notification" in row


def test_an_undelivered_draft_is_held_back_until_show_all(tmp_path) -> None:
    """A draft the user popped back to reword never reached the model, so the
    default view — what the model saw — must not show it as a turn. Its
    `queue-operation` is the log's only copy, so --show-all must.
    """
    session = _queue_session(tmp_path)
    assert "use the other flag" not in _render(session, "--skeleton")
    row = _row(_render(session, "--skeleton", "--show-all"), "use the other flag")
    assert "queue:enqueue" in row
    assert ".content" in row


def test_the_skeleton_rows_a_queued_message_once(tmp_path) -> None:
    """`enqueue` introduces the text; the `remove` that ends its wait restates
    it, as does every dequeue and popAll. Rowing those doubles the text without
    adding a block to extract.
    """
    out = _render(_queue_session(tmp_path), "--skeleton", "--show-all")
    assert out.count("wait, use --porcelain instead") == 2  # enqueue + delivery
    assert "queue:remove" not in out


# ─── Binary payloads: image and document blocks ──────────────────────────────
# A base64 payload is the one content in a log that is worthless on screen and
# ruinous in a context window: 43k chars of `iVBORw0KGg…` per screenshot. The
# render names it and hands over the command that writes the file instead.

# A real 1×1 red PNG, so the extraction recipe can be run and the result
# checked for decodability rather than only for having been written.
PNG_B64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAIAAACQd1PeAAAADElEQVR4nGP4z8AAAAMBAQ"
    "DJ/pLvAAAAAElFTkSuQmCC"
)
PNG_BYTES = 69
PDF_B64 = base64.b64encode(b"%PDF-1.5\n" + b"x" * 400 + b"\n%%EOF\n").decode()


def _image_source(b64: str = PNG_B64, media_type: str = "image/png") -> dict:
    return {"type": "base64", "media_type": media_type, "data": b64}


def _image_session(tmp_path) -> object:
    """A session carrying every shape a base64 payload reaches cc-pretty in."""
    jsonl = tmp_path / "images.jsonl"
    records = [
        {"type": "user", "uuid": "u0", "message": {"role": "user", "content": "read it"}},
        {"type": "assistant", "uuid": "a0", "message": {
            "role": "assistant", "model": "claude-opus-5", "content": [
                {"type": "tool_use", "id": "toolu_1", "name": "Read",
                 "input": {"file_path": "/tmp/chart.png"}}]}},
        # An image inside a tool_result content array — what Read and every
        # screenshot MCP server return.
        {"type": "user", "uuid": "u1", "message": {"role": "user", "content": [
            {"type": "tool_result", "tool_use_id": "toolu_1", "content": [
                {"type": "text", "text": "Read 1 image"},
                {"type": "image", "source": _image_source()}]}]}},
        # A document block standing alone on a user record — a PDF Claude Code
        # injects mid-conversation.
        {"type": "user", "uuid": "u2", "isMeta": True, "message": {
            "role": "user", "content": [
                {"type": "document",
                 "source": _image_source(PDF_B64, "application/pdf")}]}},
        # An image block standing alone, alongside text.
        {"type": "user", "uuid": "u3", "message": {"role": "user", "content": [
            {"type": "image", "source": _image_source()},
            {"type": "text", "text": "what is wrong with this?"}]}},
    ]
    jsonl.write_text("\n".join(json.dumps(r) for r in records) + "\n")
    return jsonl


def _render(jsonl, *flags: str) -> str:
    proc = _run_cli(jsonl, "--no-color", *flags)
    assert proc.returncode == 0, proc.stderr
    return proc.stdout


def test_no_base64_payload_reaches_the_render(tmp_path) -> None:
    out = _render(_image_session(tmp_path))
    # The head of each payload — present in the render means the blob is on
    # screen, truncated or whole.
    assert PNG_B64[:32] not in out
    assert PDF_B64[:32] not in out


def test_an_unbounded_tool_max_still_elides_the_payload(tmp_path) -> None:
    """--tool-max lifts truncation; it must not turn the blob back on. A
    coverage run renders at 10**9, so this is the path that check exercises."""
    out = _render(_image_session(tmp_path), "--tool-max", "1000000000")
    assert PNG_B64[:32] not in out
    assert PDF_B64[:32] not in out


def test_each_payload_is_named_by_media_type_and_decoded_size(tmp_path) -> None:
    out = _render(_image_session(tmp_path))
    assert "image/png" in out
    assert "application/pdf" in out
    # Decoded bytes, not the base64 chars encoding them: a reader sizing the
    # file to fetch wants the file's size.
    assert f"{PNG_BYTES} B" in out
    assert f"{len(PNG_B64)} B" not in out


def test_every_payload_recipe_writes_the_original_bytes(tmp_path) -> None:
    """A recipe that does not run is worse than none: it reads as truth."""
    jsonl = _image_session(tmp_path)
    out = _render(jsonl)
    recipes = [
        line.split("…file:", 1)[1].strip()
        for line in out.splitlines() if "…file:" in line
    ]
    # Three payloads in the fixture: the tool_result image, the document, the
    # standalone image.
    assert len(recipes) == 3, out

    expected = {"png": base64.b64decode(PNG_B64), "pdf": base64.b64decode(PDF_B64)}
    written = []
    for recipe in recipes:
        got = subprocess.run(["bash", "-c", recipe], cwd=tmp_path,
                             capture_output=True, text=True)
        assert got.returncode == 0, f"{recipe!r} failed: {got.stderr}"
        target = tmp_path / recipe.rsplit(">", 1)[1].strip()
        assert target.exists(), f"{recipe!r} wrote no file"
        body = target.read_bytes()
        assert body == expected[target.suffix.lstrip(".")], recipe
        written.append(target.name)
    # One file per payload — a shared name would overwrite a sibling's image.
    assert len(set(written)) == 3, written
    assert any(n.endswith(".png") for n in written)
    assert any(n.endswith(".pdf") for n in written)


def test_a_url_source_is_still_shown_verbatim(tmp_path) -> None:
    """Only the base64 blob is withheld. A URL source is the whole content of
    the block and costs nine words to print."""
    jsonl = tmp_path / "url.jsonl"
    jsonl.write_text(json.dumps({"type": "user", "message": {"role": "user", "content": [
        {"type": "image", "source": {"type": "url", "url": "https://e.com/a.png"}}]}}) + "\n")
    out = _render(jsonl)
    assert "https://e.com/a.png" in out


def test_the_skeleton_names_a_payload_instead_of_previewing_it(tmp_path) -> None:
    out = _render(_image_session(tmp_path), "--skeleton")
    assert PNG_B64[:24] not in out
    assert PDF_B64[:24] not in out
    doc_row = next(line for line in out.splitlines() if "document" in line)
    assert "application/pdf" in doc_row
    # The leaf a reader would extract from: `.` yields the base64 with it.
    assert ".source.data" in doc_row


def test_the_skeleton_result_row_names_the_payload_it_carries(tmp_path) -> None:
    """`result:Read  0~tok  ""` reads as an empty result; the image it actually
    carried is the whole reason that row exists."""
    out = _render(_image_session(tmp_path), "--skeleton")
    row = next(line for line in out.splitlines() if "result:Read" in line)
    assert "image/png" in row


def test_a_malformed_source_renders_instead_of_aborting_the_file(tmp_path) -> None:
    """A log is external input. Before `image` was modelled, a block whose
    `source` is null went through the unmodelled-block arm and rendered; a
    strict `dict` field would instead raise out of `content_blocks()` and take
    the whole session's render with it."""
    jsonl = tmp_path / "broken.jsonl"
    jsonl.write_text("\n".join(json.dumps(r) for r in [
        {"type": "user", "message": {"role": "user", "content": [
            {"type": "image", "source": None}]}},
        {"type": "user", "message": {"role": "user", "content": [
            {"type": "image"}]}},
        {"type": "assistant", "message": {"role": "assistant", "content": [
            {"type": "text", "text": "still here"}]}},
    ]) + "\n")
    out = _render(jsonl)
    assert "still here" in out
    assert out.count("◆ image") == 2
    assert "still here" in _render(jsonl, "--skeleton")


# ─── hook_success stdout (the write-only channel into a transcript) ─────────
#
# Claude Code fills `attachment.content` with a hook's stdout only when that
# stdout was not itself hook JSON — a JSON-emitting hook leaves it empty. On
# PreToolUse/PostToolUse/Stop that text never reaches the model, so the
# transcript is the only place it exists and the renderer is the only thing
# that shows it.


def _hook_success(content: str, event: str = "Stop", stdout: str | None = None) -> AttachmentRecord:
    return AttachmentRecord(
        type="attachment",
        attachment=AttachmentData(
            type="hook_success",
            hookName=event,
            hookEvent=event,
            content=content,
            stdout=content if stdout is None else stdout,
            exitCode=0,
            durationMs=4,
        ),
    )


def test_hook_success_stdout_is_printed_not_summarised_away() -> None:
    r = Renderer("/tmp/log.jsonl", tool_output_max=200, tool_input_max=200)
    out = r.render_attachment(_hook_success("<launch-provenance v1>\nsession:  s1"), ts="00:00:00", lineno=7)
    assert out is not None
    assert "hook Stop" in out
    assert "<launch-provenance v1>" in out
    assert "session:  s1" in out


def test_a_json_emitting_hook_still_renders_as_one_line() -> None:
    """The 5,000-odd PreToolUse records a real session carries keep `content`
    empty, and must not gain a body."""
    r = Renderer("/tmp/log.jsonl", tool_output_max=200, tool_input_max=200)
    out = r.render_attachment(_hook_success("", event="PreToolUse"), ts="00:00:00", lineno=7)
    assert out is not None
    assert out.count("\n") == 0


def test_long_hook_stdout_is_truncated_with_a_recovery_recipe() -> None:
    r = Renderer("/tmp/log.jsonl", tool_output_max=50, tool_input_max=200)
    out = r.render_attachment(_hook_success("P" * 4000), ts="00:00:00", lineno=9)
    assert out is not None
    assert "…full:" in out
    assert ".attachment.stdout" in out
    assert len(out) < 1000


def test_a_persisted_output_stub_is_not_what_the_reader_gets() -> None:
    """Past 10,000 chars Claude Code swaps `content` for a stub naming a file
    beside the log and holding a 2,000-char preview; `stdout` keeps the text
    itself (2.1.310 threshold `Gii = 1e4`, chunk-r1dvrqha.js:34)."""
    r = Renderer("/tmp/log.jsonl", tool_output_max=200, tool_input_max=200)
    out = r.render_attachment(
        _hook_success(
            "<persisted-output>\nOutput too large (12.4KB). Full output saved to: /x/y.txt",
            stdout="<launch-provenance v1>\nsession:  s1\n</launch-provenance v1>",
        ),
        ts="00:00:00",
        lineno=7,
    )
    assert out is not None
    assert "<launch-provenance v1>" in out
    assert "persisted-output" not in out


def test_hook_stdout_reaches_the_reader_only_under_show_all(tmp_path) -> None:
    """Its whole point is to stay out of the model's context, so the default
    view — which shows what the model was sent — must not carry it."""
    jsonl = tmp_path / "session.jsonl"
    jsonl.write_text(json.dumps({
        "type": "attachment",
        "uuid": "u1",
        "attachment": {
            "type": "hook_success", "hookName": "Stop", "hookEvent": "Stop",
            "content": "<launch-provenance v1>\nsession:  s1\n</launch-provenance v1>",
            "stdout": "<launch-provenance v1>\n", "stderr": "", "exitCode": 0,
            "command": "agent-tools hook-provenance", "durationMs": 4,
        },
        "version": "2.1.269",
    }) + "\n")
    assert "launch-provenance" not in _run_cli(jsonl).stdout
    assert "launch-provenance" in _run_cli(jsonl, "--show-all").stdout


# ─── System records that say something (2.1.289 subtype set) ────────────────
#
# Claude Code declares one constructor per transcript system subtype at
# chunk-j0tbz6ra.js:204705-204890. Most put their whole payload in `content`;
# memory_saved, api_error and the model-switch family each use fields of their
# own. A bare `[subtype]` label names the record while hiding the sentence it
# exists for, so each shape below is pinned to the text it carries.


def _system(subtype: str, **fields) -> SystemRecord:
    return SystemRecord(type="system", subtype=subtype, **fields)


def _render_sys(rec: SystemRecord, maxlen: int = 400) -> str:
    return Renderer("/tmp/log.jsonl", tool_output_max=maxlen,
                    tool_input_max=200).render_system(rec, ts="00:00:00", lineno=5)


def test_an_informational_banner_prints_what_it_said() -> None:
    out = _render_sys(_system(
        "informational",
        content="A hook blocked the turn from ending 3 consecutive times "
                "— overriding and ending turn.",
        level="warning",
    ))
    assert "informational" in out
    assert "blocked the turn from ending 3 consecutive times" in out


def test_a_loop_wakeup_entry_prints_its_notice() -> None:
    """`scheduled_task_fire` is the transcript's loop-wakeup entry."""
    out = _render_sys(_system(
        "scheduled_task_fire", content="Claude resuming /loop wakeup (Jun 4 7:09am)",
    ))
    assert "Claude resuming /loop wakeup" in out


def test_memory_saved_names_the_files_it_wrote() -> None:
    out = _render_sys(_system(
        "memory_saved", writtenPaths=["/p/memory/a.md", "/p/memory/b.md"],
    ))
    assert "/p/memory/a.md" in out
    assert "/p/memory/b.md" in out


def test_claude_codes_own_api_error_prints_the_sentence_a_human_reads() -> None:
    out = _render_sys(_system(
        "api_error",
        level="error",
        error={"message": "Connection error.",
               "formatted": "Connection refused — a firewall or proxy may be blocking it"},
        retryAttempt=2, maxRetries=10, source="request_retry",
    ))
    assert "Connection refused" in out
    assert "retry 2/10" in out


def test_an_intercept_capture_api_error_still_renders_as_a_region() -> None:
    """The capture and Claude Code share the `api_error` subtype and nothing
    else: the capture puts its text in `content` and leaves `error` unset."""
    rec = SystemRecord(
        type="system", subtype="api_error",
        content="[invalid_request_error] prompt is too long",
        detail="invalid_request_error", content_leaf="",
    )
    out = _render_sys(rec)
    assert "┌ API error" in out
    assert "invalid_request_error" in out
    assert "prompt is too long" in out


def test_a_refusal_record_carries_its_category_and_explanation() -> None:
    out = _render_sys(_system(
        "model_refusal_no_fallback",
        content="", level="warning", originalModel="claude-opus-5",
        apiRefusalCategory="reasoning_extraction",
        apiRefusalExplanation="This request was blocked as it seems to violate ...",
    ))
    assert "reasoning_extraction" in out
    assert "claude-opus-5" in out


def test_a_blocked_turn_says_so_on_the_stop_hook_summary() -> None:
    """The count alone reads as a quiet turn; the block lives in the two hook
    output lists and `preventedContinuation`."""
    out = _render_sys(_system(
        "stop_hook_summary",
        hookCount=2,
        hookInfos=[{"command": "agent-tools hook-provenance", "durationMs": 12}],
        hookErrors=["Stop hook denied continuation: report not written"],
        hookAdditionalContext=["[agent-tools] run status: 1 run still live"],
        preventedContinuation=True,
        stopReason="report not written",
    ))
    assert "hooks: 2 ran" in out
    assert "turn blocked" in out
    assert "Stop hook denied continuation" in out
    assert "run status: 1 run still live" in out


def test_a_turn_duration_record_keeps_its_one_line_shape() -> None:
    out = _render_sys(_system("turn_duration", durationMs=4200))
    assert "turn_duration: 4.2s" in out
    assert out.count("\n") == 0


def test_a_system_subtype_with_nothing_to_say_is_still_one_line() -> None:
    out = _render_sys(_system("agents_killed"))
    assert "agents_killed" in out
    assert out.count("\n") == 0


def test_a_file_history_delta_gets_a_row_not_an_unknown_record_line(tmp_path) -> None:
    """134 of these sit in the logs on this machine; before 2.1.289 was
    modelled they printed as `[unknown record: file-history-delta]`."""
    jsonl = tmp_path / "session.jsonl"
    jsonl.write_text("\n".join(json.dumps(r) for r in [
        {"type": "file-history-delta", "messageId": "m1",
         "snapshotMessageId": "s1", "trackingPath": "/w/notes.md",
         "backup": {"version": 1}},
        {"type": "assistant", "uuid": "u2", "version": "2.1.289",
         "message": {"role": "assistant", "content": [{"type": "text", "text": "done"}]}},
    ]) + "\n")
    out = _run_cli(jsonl, "--show-all").stdout
    assert "file-history delta: /w/notes.md" in out
    assert "unknown record" not in out


def test_a_null_refusal_explanation_does_not_drop_the_record() -> None:
    """Claude Code writes `apiRefusalExplanation: null` when the API gave a
    category and no prose. A field typed too narrowly fails the record out of
    `parse_all`, which hides the subtype outright rather than reporting it."""
    raw = {
        "type": "system", "uuid": "u1", "subtype": "model_refusal_fallback",
        "level": "warning", "content": "", "originalModel": "claude-opus-5",
        "apiRefusalCategory": "cyber", "apiRefusalExplanation": None,
        "version": "2.1.289",
    }
    rec = parse_record(raw)
    assert isinstance(rec, SystemRecord)
    assert "cyber" in _render_sys(rec)


def test_a_transport_api_error_names_its_status_not_its_headers() -> None:
    """A proxy failure carries `{status, headers, ...}` and no prose; the
    header dict is noise a reader cannot act on."""
    out = _render_sys(_system(
        "api_error", level="error",
        error={"status": 502, "headers": {"server": "mitmproxy 12.2.3"},
               "requestID": None, "type": None},
        retryAttempt=1, maxRetries=10,
    ))
    assert "HTTP 502" in out
    assert "mitmproxy" not in out
