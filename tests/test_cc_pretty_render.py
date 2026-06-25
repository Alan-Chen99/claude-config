from __future__ import annotations

from claude_config.cc_pretty.parse import (
    AssistantRecord,
    AttachmentData,
    AttachmentRecord,
    Message,
    Usage,
)
from claude_config.cc_pretty.render import (
    C,
    Renderer,
    fmt_ref,
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
