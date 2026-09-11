"""Pins for the proxy's SSE reassembly.

A capture is only as complete as what reassembly kept. Server-side tools deliver
their payload on `content_block_start` rather than through deltas, so a
reassembler that copies only the block's `type` writes an empty husk to disk and
no renderer can recover it.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

_PROXY = Path(__file__).resolve().parents[1] / "scripts" / "intercept" / "proxy.py"


def _load_proxy():
    spec = importlib.util.spec_from_file_location("intercept_proxy", _PROXY)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


proxy = _load_proxy()


def _sse(*events: dict) -> str:
    return "\n".join(f"data: {json.dumps(e)}" for e in events)


def _start(idx: int, block: dict) -> dict:
    return {"type": "content_block_start", "index": idx, "content_block": block}


def _delta(idx: int, delta: dict) -> dict:
    return {"type": "content_block_delta", "index": idx, "delta": delta}


def test_web_search_result_content_survives_reassembly() -> None:
    results = [
        {
            "type": "web_search_result",
            "url": "https://example.com/a",
            "title": "A result title",
        }
    ]
    msg = proxy.parse_sse_stream(
        _sse(_start(0, {"type": "web_search_tool_result", "content": results}))
    )
    assert msg["content"][0]["content"] == results


def test_server_tool_use_keeps_id_name_and_accumulates_input() -> None:
    msg = proxy.parse_sse_stream(
        _sse(
            _start(0, {"type": "server_tool_use", "id": "srv_1", "name": "web_search", "input": {}}),
            _delta(0, {"type": "input_json_delta", "partial_json": '{"query": "chrome '}),
            _delta(0, {"type": "input_json_delta", "partial_json": '136"}'}),
        )
    )
    block = msg["content"][0]
    assert block["id"] == "srv_1"
    assert block["name"] == "web_search"
    assert block["input"] == {"query": "chrome 136"}


def test_tool_use_input_comes_from_deltas_not_the_start_block() -> None:
    """Control: the start block's `input` is a placeholder, deltas are the value."""
    msg = proxy.parse_sse_stream(
        _sse(
            _start(0, {"type": "tool_use", "id": "t1", "name": "Bash", "input": {}}),
            _delta(0, {"type": "input_json_delta", "partial_json": '{"command": "ls"}'}),
        )
    )
    assert msg["content"][0] == {
        "type": "tool_use",
        "id": "t1",
        "name": "Bash",
        "input": {"command": "ls"},
    }


def test_text_and_thinking_still_accumulate() -> None:
    msg = proxy.parse_sse_stream(
        _sse(
            _start(0, {"type": "thinking", "thinking": ""}),
            _delta(0, {"type": "thinking_delta", "thinking": "a thought"}),
            _start(1, {"type": "text", "text": ""}),
            _delta(1, {"type": "text_delta", "text": "an answer"}),
        )
    )
    assert msg["content"][0]["thinking"] == "a thought"
    assert msg["content"][1]["text"] == "an answer"


def test_only_conversation_shaped_bodies_are_logged() -> None:
    """The capture filter is why every file on disk carries a messages array."""
    source = _PROXY.read_text()
    assert 'if not body.get("model") or not body.get("messages"):' in source
