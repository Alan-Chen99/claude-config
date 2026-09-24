"""Pins for the proxy's SSE reassembly and for its pass-through streaming.

A capture is only as complete as what reassembly kept. Server-side tools deliver
their payload on `content_block_start` rather than through deltas, so a
reassembler that copies only the block's `type` writes an empty husk to disk and
no renderer can recover it.

A capture is also only worth having if the session it intercepts still works.
mitmproxy buffers a whole response body by default, which holds an SSE stream --
status line included -- until the model has finished; the last two tests drive a
real mitmdump to pin both halves of the fix, the relay and the capture.
"""

from __future__ import annotations

import importlib.util
import json
import os
import socket
import subprocess
import threading
import time
import uuid
from collections.abc import Iterator
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


def test_a_refusal_keeps_its_category_and_explanation() -> None:
    """stop_details is the only record of *why* a call was refused."""
    msg = proxy.parse_sse_stream(
        _sse(
            {
                "type": "message_start",
                "message": {
                    "id": "msg_refused",
                    "model": "claude-fable-5-1",
                    "role": "assistant",
                    "usage": {"input_tokens": 2},
                },
            },
            _start(0, {"type": "thinking", "thinking": "", "signature": ""}),
            _delta(0, {"type": "thinking_delta", "thinking": "partial"}),
            {
                "type": "message_delta",
                "delta": {
                    "stop_reason": "refusal",
                    "stop_details": {
                        "type": "refusal",
                        "category": "reasoning_extraction",
                        "explanation": "This request was blocked...",
                    },
                },
                "usage": {"output_tokens": 16},
            },
        )
    )
    assert msg["stop_reason"] == "refusal"
    assert msg["stop_details"]["category"] == "reasoning_extraction"
    assert msg["stop_details"]["explanation"] == "This request was blocked..."


def test_message_level_fields_the_parser_was_never_told_about_survive() -> None:
    """The reassembly copies the message object; it does not pick from a list."""
    msg = proxy.parse_sse_stream(
        _sse(
            {
                "type": "message_start",
                "message": {
                    "id": "msg_new_shape",
                    "model": "m",
                    "role": "assistant",
                    "type": "message",
                    "container": {"id": "c-1"},
                    "context_management": {"applied_edits": []},
                    "a_field_from_a_later_release": 7,
                    "usage": {"input_tokens": 1},
                },
            },
            {"type": "message_delta", "delta": {"stop_sequence": "</done>"}, "usage": {}},
        )
    )
    assert msg["container"] == {"id": "c-1"}
    assert msg["context_management"] == {"applied_edits": []}
    assert msg["a_field_from_a_later_release"] == 7
    assert msg["stop_sequence"] == "</done>"
    assert msg["content"] == []


def test_an_api_error_body_is_kept_in_the_shape_an_in_stream_error_uses() -> None:
    detail = proxy.error_detail(
        json.dumps(
            {"type": "error", "error": {"type": "rate_limit_error", "message": "slow down"}}
        ).encode()
    )
    assert detail == {"type": "rate_limit_error", "message": "slow down"}


def test_an_error_body_that_is_not_the_api_s_is_kept_as_capped_text() -> None:
    assert proxy.error_detail(b"<html>502</html>") == {"body": "<html>502</html>"}
    assert proxy.error_detail(None) == {}
    long = proxy.error_detail(b"x" * (proxy.ERROR_BODY_MAX + 500))
    assert len(long["body"]) == proxy.ERROR_BODY_MAX


# --- Pass-through streaming ---
#
# Whether the proxy relays bytes or sits on them is a property of the running
# process, not of any function here, so these drive a real mitmdump against a
# real SSE origin. mitmproxy's default is to buffer a whole response body
# before the `response` hook and only then send the client its first byte, so
# the defect these guard against is invisible to any unit test of the addon.

_SSE_GAP = 0.25
_STREAM_EVENTS = (
    {
        "type": "message_start",
        "message": {
            "id": "msg_stream_test",
            "model": "claude-stream-test",
            "role": "assistant",
            "usage": {"input_tokens": 11},
        },
    },
    {"type": "content_block_start", "index": 0, "content_block": {"type": "text", "text": ""}},
    {"type": "content_block_delta", "index": 0, "delta": {"type": "text_delta", "text": "first "}},
    {"type": "content_block_delta", "index": 0, "delta": {"type": "text_delta", "text": "second"}},
    {
        "type": "message_delta",
        "delta": {"stop_reason": "end_turn"},
        "usage": {"output_tokens": 7},
    },
)
_ORIGIN_SPAN = _SSE_GAP * (len(_STREAM_EVENTS) - 1)


def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def _serve_sse(conn: socket.socket) -> None:
    """Answer one request with chunked SSE, one event every _SSE_GAP seconds."""
    buf = b""
    while b"\r\n\r\n" not in buf:
        received = conn.recv(65536)
        if not received:
            return
        buf += received
    head, _, body = buf.partition(b"\r\n\r\n")
    length = 0
    for line in head.split(b"\r\n"):
        if line.lower().startswith(b"content-length:"):
            length = int(line.split(b":", 1)[1])
    while len(body) < length:
        body += conn.recv(65536)

    conn.sendall(
        b"HTTP/1.1 200 OK\r\n"
        b"Content-Type: text/event-stream\r\n"
        b"Transfer-Encoding: chunked\r\n"
        b"Cache-Control: no-cache\r\n\r\n"
    )
    for index, event in enumerate(_STREAM_EVENTS):
        if index:
            time.sleep(_SSE_GAP)
        payload = f"event: {event['type']}\ndata: {json.dumps(event)}\n\n".encode()
        conn.sendall(b"%x\r\n" % len(payload) + payload + b"\r\n")
    conn.sendall(b"0\r\n\r\n")
    conn.close()


@pytest.fixture(scope="module")
def sse_origin() -> Iterator[int]:
    listener = socket.socket()
    listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    listener.bind(("127.0.0.1", 0))
    listener.listen(8)

    def accept_loop() -> None:
        while True:
            try:
                conn, _ = listener.accept()
            except OSError:
                return
            threading.Thread(target=_serve_sse, args=(conn,), daemon=True).start()

    threading.Thread(target=accept_loop, daemon=True).start()
    yield listener.getsockname()[1]
    listener.close()


@pytest.fixture(scope="module")
def proxy_process(tmp_path_factory) -> Iterator[tuple[int, Path]]:
    """A real mitmdump running the addon, with HOME -- and so the log tree
    write_log() derives from Path.home() -- pointed at a scratch directory."""
    home = tmp_path_factory.mktemp("intercept-home")
    port = _free_port()
    process = subprocess.Popen(
        ["mitmdump", "-s", str(_PROXY), "-p", str(port), "--listen-host", "127.0.0.1", "-q"],
        env={**os.environ, "HOME": str(home)},
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    deadline = time.monotonic() + 30
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise AssertionError(f"mitmdump exited early: {process.communicate()[0]}")
        try:
            socket.create_connection(("127.0.0.1", port), timeout=0.3).close()
            break
        except OSError:
            time.sleep(0.1)
    else:
        process.kill()
        raise AssertionError("mitmdump never accepted connections")

    yield port, home

    process.terminate()
    process.wait(timeout=15)


def _post_through_proxy(proxy_port: int, origin_port: int, session_id: str) -> list[tuple[float, bytes]]:
    """POST a conversation-shaped body and timestamp every arrival.

    The Host header is what the addon filters on (mitmproxy's
    Request.pretty_host prefers it over the destination address), so a local
    origin can stand in for api.anthropic.com without touching DNS.
    """
    body = json.dumps(
        {"model": "claude-stream-test", "messages": [{"role": "user", "content": "hi"}], "stream": True}
    ).encode()
    request = (
        f"POST http://127.0.0.1:{origin_port}/v1/messages HTTP/1.1\r\n"
        f"Host: {proxy.TARGET_HOST}\r\n"
        f"{proxy.SESSION_HEADER}: {session_id}\r\n"
        "Content-Type: application/json\r\n"
        f"Content-Length: {len(body)}\r\n"
        "Connection: close\r\n\r\n"
    ).encode() + body

    started = time.monotonic()
    arrivals: list[tuple[float, bytes]] = []
    with socket.create_connection(("127.0.0.1", proxy_port), timeout=30) as sock:
        sock.sendall(request)
        while True:
            received = sock.recv(65536)
            if not received:
                break
            arrivals.append((time.monotonic() - started, received))
    return arrivals


def test_sse_events_reach_the_client_before_the_response_ends(sse_origin, proxy_process) -> None:
    """The defect: mitmproxy holds every byte, status line included, to the end."""
    proxy_port, _ = proxy_process
    arrivals = _post_through_proxy(proxy_port, sse_origin, str(uuid.uuid4()))

    assert arrivals, "no response reached the client"
    carrying_events = [at for at, data in arrivals if b"data: " in data]
    assert len(carrying_events) >= 2, (
        f"events arrived in {len(carrying_events)} delivery(s); a buffering proxy "
        f"delivers exactly one: {[(at, len(d)) for at, d in arrivals]}"
    )
    assert arrivals[0][0] < _ORIGIN_SPAN, (
        f"first byte took {arrivals[0][0]:.3f}s, past the origin's own "
        f"{_ORIGIN_SPAN:.3f}s of emitting -- the response was buffered"
    )


def test_a_streamed_response_is_still_logged_in_full(sse_origin, proxy_process) -> None:
    """Streaming past mitmproxy's buffer must not cost the capture its body."""
    proxy_port, home = proxy_process
    session_id = str(uuid.uuid4())
    _post_through_proxy(proxy_port, sse_origin, session_id)

    log_file = home / ".claude" / "requests-log" / session_id / "0001.json"
    deadline = time.monotonic() + 10
    while not log_file.exists() and time.monotonic() < deadline:
        time.sleep(0.1)
    assert log_file.exists(), f"no capture written to {log_file}"

    entry = json.loads(log_file.read_text())
    assert entry["streaming"] is True
    assert entry["request"]["model"] == "claude-stream-test"
    assert entry["response"]["id"] == "msg_stream_test"
    assert entry["response"]["content"] == [{"type": "text", "text": "first second"}]
    assert entry["response"]["stop_reason"] == "end_turn"
    assert entry["response"]["usage"] == {"input_tokens": 11, "output_tokens": 7}


@pytest.fixture(scope="module")
def error_origin() -> Iterator[int]:
    """An origin that refuses every call the way the API refuses one."""
    body = json.dumps(
        {"type": "error", "error": {"type": "rate_limit_error", "message": "requires usage credits"}}
    ).encode()
    listener = socket.socket()
    listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    listener.bind(("127.0.0.1", 0))
    listener.listen(8)

    def serve(conn: socket.socket) -> None:
        buf = b""
        while b"\r\n\r\n" not in buf:
            received = conn.recv(65536)
            if not received:
                conn.close()
                return
            buf += received
        conn.sendall(
            b"HTTP/1.1 429 Too Many Requests\r\nContent-Type: application/json\r\n"
            b"Content-Length: %d\r\nConnection: close\r\n\r\n" % len(body) + body
        )
        conn.close()

    def accept_loop() -> None:
        while True:
            try:
                conn, _ = listener.accept()
            except OSError:
                return
            threading.Thread(target=serve, args=(conn,), daemon=True).start()

    threading.Thread(target=accept_loop, daemon=True).start()
    yield listener.getsockname()[1]
    listener.close()


def test_a_refused_call_is_logged_with_the_api_s_own_reason(error_origin, proxy_process) -> None:
    """A status line alone names neither the limit hit nor the field rejected."""
    proxy_port, home = proxy_process
    session_id = str(uuid.uuid4())
    _post_through_proxy(proxy_port, error_origin, session_id)

    log_file = home / ".claude" / "requests-log" / session_id / "0001.json"
    deadline = time.monotonic() + 10
    while not log_file.exists() and time.monotonic() < deadline:
        time.sleep(0.1)
    assert log_file.exists(), f"no capture written to {log_file}"

    entry = json.loads(log_file.read_text())
    assert "response" not in entry
    assert entry["error"] == {
        "status": 429,
        "statusText": "Too Many Requests",
        "type": "rate_limit_error",
        "message": "requires usage credits",
    }
    assert entry["request"]["model"] == "claude-stream-test"
