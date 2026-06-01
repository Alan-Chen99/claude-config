from __future__ import annotations

from claude_config.cc_pretty.render import trunc


def test_trunc_short_string_returns_unchanged() -> None:
    assert trunc("hello", 100) == "hello"


def test_trunc_long_string_without_next_step_uses_head_tail() -> None:
    s = "A" * 500 + "B" * 500 + "C" * 500
    out = trunc(s, 90)
    # Head 60 chars + omission + tail 30 chars (approx — exact split is
    # 2/3 head, 1/3 tail; the assertions below check the structure only).
    assert out.startswith("A")
    assert out.endswith("C" * 10)
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
