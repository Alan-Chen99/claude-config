"""Pins for "the render shows what the source carries".

Two halves. The first pins each renderer fix that made the invariant true: a
truncation that ignored --tool-max, a block type that vanished, a capture that
would not load. The second pins the checker that catches the next such defect —
a checker only ever reporting "clean" proves nothing, so each finding kind is
exercised against input that must produce it.
"""

from __future__ import annotations

import json

import pytest

from claude_config.cc_pretty.coverage import (
    UNBOUNDED,
    _findings_for,
    check_path,
    intercept_needles,
    jsonl_needles,
    normalize,
    run,
)
from claude_config.cc_pretty.parse import (
    AttachmentData,
    AttachmentRecord,
    ToolResultBlock,
    ToolUseResultDict,
    parse_content_block,
)
from claude_config.cc_pretty.render import C, Renderer
from claude_config.cc_pretty_intercept.main import _render_message, _render_response
from claude_config.cc_pretty_intercept.parse import Message, Response, load_intercept

C.disable()  # All tests assert on plain text — no ANSI escapes.

MARKER = "more chars"


def _renderer(maxlen: int = UNBOUNDED) -> Renderer:
    return Renderer("/tmp/x.jsonl", tool_output_max=maxlen, tool_input_max=maxlen)


# ── Renderer: nothing truncates at a large --tool-max ────────────────────────


def test_tool_result_stderr_scales_with_tool_max() -> None:
    block = ToolResultBlock(type="tool_result", tool_use_id="t1", content="body")
    tur = ToolUseResultDict(stdout="", stderr="E" * 500)
    out = _renderer()._render_tool_result(block, 1, 0, tur=tur)
    assert MARKER not in out
    assert "E" * 500 in out


def test_string_tool_use_result_that_repeats_the_block_is_not_echoed() -> None:
    """The block is built from the same value, so the echo only repeated it."""
    body = "File content (41204 tokens) exceeds maximum allowed tokens (25000)."
    block = ToolResultBlock(type="tool_result", tool_use_id="t1", content=body)
    out = _renderer()._render_tool_result(block, 1, 0, tur=body)
    assert out.count(body) == 1
    assert MARKER not in out


def test_string_tool_use_result_that_diverges_is_shown_in_full() -> None:
    """A permission denial words the marker differently from the block."""
    block = ToolResultBlock(
        type="tool_result",
        tool_use_id="t1",
        content="The user doesn't want to proceed with this tool use.",
    )
    out = _renderer()._render_tool_result(block, 1, 0, tur="User rejected tool use")
    assert "User rejected tool use" in out
    assert MARKER not in out


def test_hook_error_stderr_scales_with_tool_max() -> None:
    rec = AttachmentRecord(
        type="attachment",
        attachment=AttachmentData(
            type="hook_non_blocking_error", hookName="h", stderr="E" * 400
        ),
    )
    out = _renderer().render_attachment(rec, 1, "00:00:00")
    assert MARKER not in out
    assert "E" * 400 in out


def test_queued_command_prompt_scales_with_tool_max() -> None:
    prompt = "P" * 300
    rec = AttachmentRecord(
        type="attachment",
        attachment=AttachmentData(
            type="queued_command", prompt=prompt, commandMode="prompt"
        ),
    )
    out = _renderer().render_attachment(rec, 1, "00:00:00")
    assert MARKER not in out
    assert prompt in out


def test_small_tool_max_still_truncates() -> None:
    """Control: the limits track the flag rather than being removed."""
    block = ToolResultBlock(type="tool_result", tool_use_id="t1", content="body")
    out = _renderer(80)._render_tool_result(block, 1, 0, tur=ToolUseResultDict(stderr="E" * 500))
    assert MARKER in out


# ── Renderer: unmodelled block types show their payload ──────────────────────

SERVER_TOOL_USE = {
    "type": "server_tool_use",
    "id": "srvtoolu_1",
    "name": "web_search",
    "input": {"query": "Chrome 136 remote-debugging-port"},
}


def test_unknown_block_payload_is_rendered_not_dropped() -> None:
    out = _renderer()._render_unknown_block(parse_content_block(SERVER_TOOL_USE), 1, 0)
    assert "server_tool_use" in out
    assert "Chrome 136 remote-debugging-port" in out


def test_intercept_message_renders_unknown_block_payload() -> None:
    msg = Message(role="assistant", content=[SERVER_TOOL_USE])
    out = _render_message(msg, 0, 1, _renderer(), lineno=3)
    assert "Chrome 136 remote-debugging-port" in out


def test_intercept_response_renders_unknown_block_payload() -> None:
    resp = Response(model="m", content=[SERVER_TOOL_USE])
    out = _render_response(resp, _renderer())
    assert "Chrome 136 remote-debugging-port" in out


def test_assistant_turn_renders_unknown_block_payload() -> None:
    from claude_config.cc_pretty.parse import AssistantRecord
    from claude_config.cc_pretty.parse import Message as JsonlMessage

    rec = AssistantRecord(
        type="assistant",
        message=JsonlMessage(role="assistant", content=[SERVER_TOOL_USE]),
    )
    out = _renderer().render_assistant_turn([(rec, 1)], "00:00:00")
    assert "Chrome 136 remote-debugging-port" in out


# ── Loader: an HTTP failure still carries a renderable request ───────────────


def _write(tmp_path, name: str, payload: dict) -> str:
    path = tmp_path / name
    path.write_text(json.dumps(payload, indent=2))
    return str(path)


ERROR_CAPTURE = {
    "timestamp": "2026-01-01T00:00:00Z",
    "streaming": True,
    "error": {"status": 429, "statusText": "Too Many Requests"},
    "request": {
        "model": "claude-opus-5",
        "messages": [{"role": "user", "content": "the question that never got an answer"}],
    },
}


def test_error_shaped_capture_loads(tmp_path) -> None:
    log = load_intercept(_write(tmp_path, "err.json", ERROR_CAPTURE))
    assert log.response is None
    assert log.error.status == 429
    assert log.request.messages[0].content == "the question that never got an answer"


def test_capture_without_response_or_error_is_rejected(tmp_path) -> None:
    with pytest.raises(ValueError, match="needs 'request' plus 'response' or 'error'"):
        load_intercept(_write(tmp_path, "bad.json", {"request": {"model": "m"}}))


def test_otel_span_is_named_as_such(tmp_path) -> None:
    span = {"spanContext": {"traceId": "x"}, "attributes": {}, "events": []}
    with pytest.raises(ValueError, match="OTEL span export"):
        load_intercept(_write(tmp_path, "span.json", span))


# ── Checker: each finding kind fires on input that must produce it ───────────


def test_checker_reports_renderer_truncation() -> None:
    findings = _findings_for(
        "f.json", "source with no marker", "body ... [91 more chars] ... tail", []
    )
    assert [f.kind for f in findings] == ["renderer_truncation"]


def test_checker_ignores_a_marker_that_came_from_the_source() -> None:
    """Sessions here capture cc-pretty output as tool results; those are data."""
    marker = " ... [91 more chars] ... "
    findings = _findings_for("f.json", f"source holds {marker}", f"render holds {marker}", [])
    assert findings == []


def test_checker_reports_missing_content() -> None:
    findings = _findings_for("f.json", "", "rendered output", [(".a.b", "absent text")])
    assert [f.kind for f in findings] == ["missing_content"]
    assert ".a.b" in findings[0].detail


def test_checker_accepts_content_the_renderer_indented() -> None:
    findings = _findings_for("f.json", "", "  │ line one\n  │ line two", [(".t", "line one\nline two")])
    assert findings == []


def test_checker_reports_load_error(tmp_path) -> None:
    path = tmp_path / "notacapture.json"
    path.write_text(json.dumps({"spanContext": {}}))
    findings = check_path(str(path))
    assert [f.kind for f in findings] == ["load_error"]


def test_checker_passes_a_capture_carrying_an_unmodelled_block(tmp_path) -> None:
    capture = {
        "request": {"model": "m", "messages": [{"role": "user", "content": "hi"}]},
        "response": {"model": "m", "content": [SERVER_TOOL_USE]},
    }
    assert run([_write(tmp_path, "ok.json", capture)]).ok


def test_checker_passes_an_error_shaped_capture(tmp_path) -> None:
    assert run([_write(tmp_path, "err.json", ERROR_CAPTURE)]).ok


# ── Needle extraction ────────────────────────────────────────────────────────


def test_intercept_needles_cover_every_conversation_block() -> None:
    capture = {
        "request": {
            "messages": [
                {"role": "user", "content": "plain string"},
                {
                    "role": "assistant",
                    "content": [
                        {"type": "text", "text": "some text"},
                        {"type": "thinking", "thinking": "some thought"},
                        {"type": "tool_use", "input": {"cmd": "ls -la"}},
                    ],
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "tool_result", "content": [{"type": "text", "text": "out"}]}
                    ],
                },
            ]
        },
        "response": {"content": [SERVER_TOOL_USE]},
    }
    texts = [t for _, t in intercept_needles(capture)]
    assert "plain string" in texts
    assert "some text" in texts
    assert "some thought" in texts
    assert "ls -la" in texts
    assert "out" in texts
    assert any("Chrome 136" in t for t in texts)


def test_jsonl_needles_skip_non_conversation_records() -> None:
    records = [
        ({"type": "assistant", "message": {"content": [{"type": "text", "text": "kept"}]}}, 1),
        ({"type": "progress", "message": {"content": [{"type": "text", "text": "dropped"}]}}, 2),
    ]
    texts = [t for _, t in jsonl_needles(records)]
    assert texts == ["kept"]


def test_jsonl_needle_paths_carry_the_source_line() -> None:
    records = [({"type": "assistant", "message": {"content": [{"type": "text", "text": "x"}]}}, 42)]
    assert jsonl_needles(records)[0][0].startswith("L42.")


def test_normalize_drops_indent_and_box_decoration() -> None:
    assert normalize("    │ a\n\n      b  ") == "a\nb"


# ── Skeleton: an unmodelled block gets a row, not silence ────────────────────


def test_skeleton_lists_an_unmodelled_block() -> None:
    from claude_config.cc_pretty.parse import AssistantRecord
    from claude_config.cc_pretty.parse import Message as JsonlMessage
    from claude_config.cc_pretty.render import render_skeleton

    rec = AssistantRecord(
        type="assistant",
        message=JsonlMessage(role="assistant", content=[SERVER_TOOL_USE]),
    )
    out = render_skeleton(
        [(rec, 1)],
        log_path="/tmp/x.jsonl",
        compact_hidden=set(),
        hidden_for_rewind=set(),
        compaction_markers={},
        rewind_markers={},
        record_visible=lambda _rec: True,
    )
    # The skeleton is a density map: every row is ref + label + size + jq leaf
    # + a 50-char preview, so the assertion is that the block gets a row and a
    # leaf to extract it by, not that its payload is spelled out here.
    assert "block:server_tool_use" in out
    assert "web_search" in out
    row = next(line for line in out.splitlines() if "block:server_tool_use" in line)
    assert "@L1" in row
    assert " . " in row
