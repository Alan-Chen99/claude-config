"""cc-pretty-intercept renders a capture through the shared cc-pretty pipeline.

Everything here drives ``main()`` end-to-end against a capture on disk, because
that is the only level at which the properties under test are real: the flag
surface, the color decision and the jq recovery recipes are all decided between
argparse and ``run_pipeline``.
"""

from __future__ import annotations

import io
import json
import subprocess
import sys
from contextlib import redirect_stdout

import pytest

from claude_config.cc_pretty_intercept.main import main

THINKING = {"type": "thinking", "thinking": "some thought", "signature": "sig"}


def capture(**over) -> dict:
    """A minimal well-formed capture, overridable key by key."""
    base = {
        "timestamp": "2026-09-13T02:43:24+00:00",
        "duration_ms": 343,
        "session": {"session_id": "d971c95a-0000-0000-0000-000000000000"},
        "streaming": False,
        "request": {
            "model": "claude-test",
            "system": [{"type": "text", "text": "SYSTEM-PROMPT-BODY"}],
            "tools": [{"name": "Bash"}, {"name": "Read"}],
            "messages": [{"role": "user", "content": "hello there"}],
        },
        "response": {"model": "claude-test", "content": [{"type": "text", "text": "hi"}]},
    }
    base.update(over)
    return base


def render(tmp_path, cap: dict, *flags: str) -> str:
    path = tmp_path / "0001.json"
    path.write_text(json.dumps(cap))
    buf = io.StringIO()
    with redirect_stdout(buf):
        main([str(path), *flags])
    return buf.getvalue()


# ── Content the capture carried reaches the render ──────────────────────────


def test_a_request_message_s_thinking_block_renders_with_its_own_ref(tmp_path) -> None:
    cap = capture()
    cap["request"]["messages"] = [
        {"role": "user", "content": "go"},
        {"role": "assistant", "content": [THINKING]},
    ]
    out = render(tmp_path, cap)
    assert "╭─ thinking" in out
    assert "some thought" in out


def test_the_response_s_thinking_block_renders(tmp_path) -> None:
    cap = capture()
    cap["response"]["content"] = [THINKING]
    out = render(tmp_path, cap)
    assert "╭─ thinking" in out
    assert "some thought" in out


def test_the_system_prompt_and_tool_list_are_shown_by_default(tmp_path) -> None:
    """They are the content the call was made of, not bookkeeping."""
    out = render(tmp_path, capture())
    assert "SYSTEM-PROMPT-BODY" in out
    assert "Bash, Read" in out


def test_no_system_and_no_tools_drop_their_regions(tmp_path) -> None:
    out = render(tmp_path, capture(), "--no-system", "--no-tools")
    assert "SYSTEM-PROMPT-BODY" not in out
    assert "Bash, Read" not in out
    assert "hello there" in out


def test_a_refusal_shows_why_it_was_refused(tmp_path) -> None:
    """stop:refusal alone says a call died, not what killed it."""
    cap = capture()
    cap["response"] = {
        "model": "claude-fable-5-1",
        "content": [],
        "stop_reason": "refusal",
        "stop_details": {
            "type": "refusal",
            "category": "reasoning_extraction",
            "explanation": "This request was blocked...",
        },
    }
    out = render(tmp_path, cap)
    assert "reasoning_extraction" in out
    assert "This request was blocked..." in out


def test_a_refused_call_renders_the_api_s_own_reason(tmp_path) -> None:
    cap = capture()
    del cap["response"]
    cap["error"] = {
        "status": 429,
        "statusText": "Too Many Requests",
        "type": "rate_limit_error",
        "message": "requires usage credits",
    }
    out = render(tmp_path, cap)
    assert "HTTP 429 Too Many Requests" in out
    assert "[rate_limit_error] requires usage credits" in out


def test_an_error_body_that_was_not_the_api_s_still_renders(tmp_path) -> None:
    cap = capture()
    del cap["response"]
    cap["error"] = {"status": 502, "statusText": "Bad Gateway", "body": "<html>"}
    out = render(tmp_path, cap)
    assert "HTTP 502 Bad Gateway" in out
    assert "<html>" in out


def test_an_assistant_message_carrying_a_bare_string_still_renders(tmp_path) -> None:
    """The API permits a prefill; content_blocks() yields nothing for one."""
    cap = capture()
    cap["request"]["messages"] = [
        {"role": "user", "content": "go"},
        {"role": "assistant", "content": "PREFILLED-TEXT"},
    ]
    assert "PREFILLED-TEXT" in render(tmp_path, cap)


# ── Refs address the capture, and the recipes under them run ────────────────


def test_each_record_gets_its_own_ref(tmp_path) -> None:
    """Every ref was @L1 while the renderer was driven a message at a time."""
    cap = capture()
    cap["request"]["messages"] = [
        {"role": "user", "content": f"message {i}"} for i in range(4)
    ]
    out = render(tmp_path, cap, "--skeleton")
    refs = {line.split()[0] for line in out.splitlines() if line.startswith("@L")}
    assert len(refs) >= 7  # 1 system + 1 tools + 4 messages + 1 response


def _truncating_capture() -> dict:
    """A capture whose every addressable body exceeds a small --tool-max."""
    cap = capture()
    cap["request"]["system"] = [{"type": "text", "text": "S" * 400}]
    cap["request"]["messages"] = [
        {"role": "user", "content": "go"},
        {"role": "assistant", "content": [
            {"type": "tool_use", "id": "t1", "name": "Bash", "input": {"cmd": "x" * 400}},
        ]},
        {"role": "user", "content": [
            {"type": "tool_result", "tool_use_id": "t1", "content": "o" * 400},
        ]},
    ]
    return cap


def test_every_recovery_recipe_runs_against_the_capture(tmp_path) -> None:
    """A recipe that does not run is worse than no recipe: it reads as truth."""
    cap = _truncating_capture()
    path = tmp_path / "0001.json"
    path.write_text(json.dumps(cap))
    buf = io.StringIO()
    with redirect_stdout(buf):
        main([str(path), "--tool-max", "50"])

    recipes = {
        line.split("jq -r '", 1)[1].split("'", 1)[0]
        for line in buf.getvalue().splitlines()
        if "jq -r '" in line
    }
    runnable = {r for r in recipes if "<" not in r}  # the legend's template is not one
    assert runnable, "no recovery recipes were emitted"
    for expr in runnable:
        got = subprocess.run(
            ["jq", "-r", expr, str(path)], capture_output=True, text=True,
        )
        assert got.returncode == 0, f"{expr!r} failed: {got.stderr}"
        assert got.stdout.strip() not in ("", "null"), f"{expr!r} extracted nothing"


def test_every_skeleton_row_names_a_leaf_that_exists_in_the_capture(tmp_path) -> None:
    """A skeleton row is a jq plan: ref plus leaf, assembled by the reader."""
    cap = _truncating_capture()
    path = tmp_path / "0001.json"
    path.write_text(json.dumps(cap))
    buf = io.StringIO()
    with redirect_stdout(buf):
        main([str(path), "--skeleton"])

    leaves = set()
    for line in buf.getvalue().splitlines():
        if not line.startswith("@L"):
            continue
        cols = line.split()
        leaves.update(c for c in cols if c.startswith("."))
    assert leaves, "skeleton emitted no rows"
    # cc's own leaves address a JSONL record and do not exist in a capture.
    assert ".message.content" not in leaves
    assert ".state.output" not in leaves
    assert leaves <= {".text", ".input", ".content", ".thinking"}


def test_the_recipes_address_the_capture_s_own_shape(tmp_path) -> None:
    """A capture is one pretty-printed object; `sed -n 1p` yields `{`."""
    cap = capture()
    cap["request"]["system"] = [{"type": "text", "text": "S" * 400}]
    out = render(tmp_path, cap, "--tool-max", "50")
    assert "sed -n" not in out
    assert ".request.system[0].text" in out


# ── Output decisions match the other two front-ends ─────────────────────────


def test_color_is_off_when_stdout_is_not_a_tty(tmp_path) -> None:
    assert "\x1b[" not in render(tmp_path, capture())


def test_color_forced_on_reaches_a_redirected_stdout(tmp_path) -> None:
    """Out of process: C.disable() is a one-way class mutation another test
    module performs at import, so in-process the flag cannot be observed."""
    path = tmp_path / "0001.json"
    path.write_text(json.dumps(capture()))
    got = subprocess.run(
        [sys.executable, "-c",
         "from claude_config.cc_pretty_intercept.main import main;"
         f"main([{str(path)!r}, '--color'])"],
        capture_output=True, text=True,
    )
    assert got.returncode == 0, got.stderr
    assert "\x1b[" in got.stdout


def test_the_header_reports_the_call_in_every_density(tmp_path) -> None:
    for flags in ((), ("--skeleton",)):
        out = render(tmp_path, capture(), *flags)
        assert "claude-test" in out
        assert "non-stream" in out


def test_chat_only_drops_the_regions_that_are_not_the_exchange(tmp_path) -> None:
    out = render(tmp_path, capture(), "--chat-only")
    assert "hello there" in out
    assert "SYSTEM-PROMPT-BODY" not in out


def test_show_usage_surfaces_the_response_s_token_counts(tmp_path) -> None:
    cap = capture()
    cap["response"]["usage"] = {"input_tokens": 1234, "output_tokens": 7}
    assert "in:1,234" not in render(tmp_path, capture())
    assert "in:1,234" in render(tmp_path, cap, "--show-usage")


def test_validate_only_reports_the_record_count_and_exits_clean(tmp_path) -> None:
    path = tmp_path / "0001.json"
    path.write_text(json.dumps(capture()))
    with pytest.raises(SystemExit) as exc:
        main([str(path), "--validate-only"])
    assert exc.value.code == 0


def test_agent_mode_chunks_a_render_too_big_to_print(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("BASH_MAX_OUTPUT_LENGTH", "500")
    cap = capture()
    cap["request"]["messages"] = [
        {"role": "user", "content": "x" * 2000} for _ in range(4)
    ]
    out = render(tmp_path, cap, "--agent")
    assert "Chunk files (read selectively):" in out
    assert "cc-pretty-intercept" in out
