"""Smoke-pin cc-pretty-intercept's thinking-block render paths.

_render_message / _render_response call Renderer._render_thinking with the
ref-carrying (block, lineno, block_idx) signature. A signature drift in
render.py must fail here, not crash the CLI at runtime (see bf4bf53).
"""

from __future__ import annotations

from claude_config.cc_pretty.render import C, Renderer
from claude_config.cc_pretty_intercept.main import (
    _render_message,
    _render_response,
    _render_transport_error,
)
from claude_config.cc_pretty_intercept.parse import Message, Response, TransportError

C.disable()  # All tests assert on plain text — no ANSI escapes.


def _thinking_block() -> dict:
    return {"type": "thinking", "thinking": "some thought", "signature": "sig"}


def _renderer() -> Renderer:
    return Renderer("/tmp/x.json", tool_output_max=2000, tool_input_max=2000)


def test_render_message_thinking_block_renders_with_ref() -> None:
    msg = Message(role="assistant", content=[_thinking_block()])
    out = _render_message(msg, 0, 1, _renderer(), lineno=7)
    assert "╭─ thinking" in out
    assert "some thought" in out
    # bi=0 is omitted from the ref; lineno threads through to the header.
    assert "@L7" in out


def test_render_response_thinking_block_renders_with_ref() -> None:
    resp = Response(model="claude-test", content=[_thinking_block()])
    out = _render_response(resp, _renderer())
    assert "╭─ thinking" in out
    assert "some thought" in out
    # Response blocks have no JSONL line; the call site passes lineno=1.
    assert "@L1" in out


def test_a_refusal_shows_why_it_was_refused() -> None:
    """stop:refusal alone says a call died, not what killed it."""
    resp = Response(
        model="claude-fable-5-1",
        content=[],
        stop_reason="refusal",
        stop_details={
            "type": "refusal",
            "category": "reasoning_extraction",
            "explanation": "This request was blocked...",
        },
    )
    out = _render_response(resp, _renderer())
    assert "stop:refusal" in out
    assert "reasoning_extraction" in out
    assert "This request was blocked..." in out


def test_a_refused_call_renders_the_api_s_own_reason() -> None:
    out = _render_transport_error(
        TransportError(
            status=429,
            statusText="Too Many Requests",
            type="rate_limit_error",
            message="requires usage credits",
        )
    )
    assert "HTTP 429 Too Many Requests" in out
    assert "[rate_limit_error] requires usage credits" in out


def test_an_error_body_that_was_not_the_api_s_still_renders() -> None:
    out = _render_transport_error(TransportError(status=502, statusText="Bad Gateway", body="<html>"))
    assert "HTTP 502 Bad Gateway" in out
    assert "<html>" in out
