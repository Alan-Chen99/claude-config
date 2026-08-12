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
    Usage,
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
    oc = "\n".join(legend_lines("opencode://ses_x"))
    for token in (".text", ".state.input", ".state.output",
                  "opencode export ses_x"):
        assert token in oc, token
    oc_file = "\n".join(legend_lines("opencode-file:///tmp/x.json"))
    assert "opencode export" not in oc_file
    assert "jq -r" in oc_file and "/tmp/x.json" in oc_file
