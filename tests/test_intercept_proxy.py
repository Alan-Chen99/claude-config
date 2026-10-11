"""Pins for the proxy's SSE reassembly and for its pass-through streaming.

A capture is only as complete as what reassembly kept. Server-side tools deliver
their payload on `content_block_start` rather than through deltas, so a
reassembler that copies only the block's `type` writes an empty husk to disk and
no renderer can recover it.

A capture is also only worth having if the session it intercepts still works.
mitmproxy buffers a whole response body by default, which holds an SSE stream --
status line included -- until the model has finished; the tests from "Pass-through
streaming" on drive a real mitmdump to pin both halves of the fix, the relay and
the capture.
"""

from __future__ import annotations

import base64
import gzip
import itertools
import json
import os
import socket
import subprocess
import threading
import time
import uuid
import zlib
from collections.abc import Callable, Iterator
from pathlib import Path

import brotli
import pytest
import zstandard
from hypothesis import given, strategies as st

from claude_config.cc_replay.proxy_module import load_proxy

_PROXY = Path(__file__).resolve().parents[1] / "scripts" / "intercept" / "proxy.py"


proxy = load_proxy()


def _sse(*events: dict) -> str:
    return "\n".join(f"data: {json.dumps(e)}" for e in events)


def _start(idx: int, block: dict) -> dict:
    return {"type": "content_block_start", "index": idx, "content_block": block}


def _delta(idx: int, delta: dict) -> dict:
    return {"type": "content_block_delta", "index": idx, "delta": delta}


def _sse_no_space(*events: dict) -> str:
    """SSE as the Kimi endpoint sends it: no space after `data:`."""
    return "\n".join(f"data:{json.dumps(e)}" for e in events)


def test_a_stream_without_the_space_after_data_is_still_reassembled() -> None:
    """The space is optional per the SSE spec, and one provider omits it.

    Requiring it skipped every line, and the all-defaults message that came out
    was written to disk as if it were a real empty turn.
    """
    events = (
        {"type": "message_start", "message": {"id": "msg_1", "model": "k3", "usage": {}}},
        _start(0, {"type": "text", "text": ""}),
        _delta(0, {"type": "text_delta", "text": "CAPTURED"}),
        {"type": "message_delta", "delta": {"stop_reason": "end_turn"}},
    )
    msg = proxy.parse_sse_stream(_sse_no_space(*events))

    assert msg["model"] == "k3"
    assert msg["stop_reason"] == "end_turn"
    assert msg["content"][0]["text"] == "CAPTURED"
    assert msg == proxy.parse_sse_stream(_sse(*events))


def test_a_stream_nothing_parsed_out_of_raises_instead_of_capturing_defaults() -> None:
    """An all-defaults message on disk is indistinguishable from a real empty turn."""
    with pytest.raises(ValueError):
        proxy.parse_sse_stream("event:message_start\nsomething that is not SSE\n")


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


# --- Failed-call detail: trigger classification and chunk decoding ---


def test_soft_error_trigger_fires_on_a_refusal_and_keeps_its_details() -> None:
    trigger = proxy.soft_error_trigger(
        {
            "stop_reason": "refusal",
            "stop_details": {"category": "reasoning_extraction", "explanation": "x"},
        }
    )
    assert trigger == {
        "kind": "refusal",
        "stop_reason": "refusal",
        "stop_details": {"category": "reasoning_extraction", "explanation": "x"},
    }


def test_soft_error_trigger_fires_on_an_in_stream_error() -> None:
    trigger = proxy.soft_error_trigger({"error": {"type": "overloaded_error"}})
    assert trigger == {"kind": "stream_error", "error": {"type": "overloaded_error"}}


def test_soft_error_trigger_is_none_for_an_ordinary_completion() -> None:
    assert proxy.soft_error_trigger({"stop_reason": "end_turn", "error": None}) is None
    assert proxy.soft_error_trigger({"stop_reason": "max_tokens"}) is None
    assert proxy.soft_error_trigger({"stop_reason": "tool_use"}) is None


# Every coding Claude Code's Accept-Encoding offers. The API answers SSE in gzip
# and JSON in br, so the relay sees compressed reads, not text.
_ENCODE: dict[str, Callable[[bytes], bytes]] = {
    "identity": lambda data: data,
    "gzip": gzip.compress,
    "deflate": zlib.compress,
    "br": brotli.compress,
    "zstd": lambda data: zstandard.ZstdCompressor().compress(data),
}


@given(
    text=st.text(),
    coding=st.sampled_from(sorted(_ENCODE)),
    cuts=st.lists(st.integers(min_value=0)),
)
def test_chunk_texts_rebuild_the_body_wherever_the_wire_split(text, coding, cuts) -> None:
    """A read can end inside a compressed block or inside a UTF-8 character;
    neither may cost a byte or leave a replacement character behind."""
    wire = _ENCODE[coding](text.encode())
    bounds = sorted({0, len(wire), *(cut % (len(wire) + 1) for cut in cuts)})
    meta = [(10 * i, end - start) for i, (start, end) in enumerate(itertools.pairwise(bounds))]

    raw, chunks = proxy.decode_chunks(wire, meta, coding)

    assert raw == text
    assert "".join(chunk["text"] for chunk in chunks) == text
    assert [(chunk["offset_ms"], chunk["bytes"]) for chunk in chunks] == meta


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


def _read_request(conn: socket.socket) -> bool:
    """Consume one request, body included; False when the client hung up first."""
    buf = b""
    while b"\r\n\r\n" not in buf:
        received = conn.recv(65536)
        if not received:
            return False
        buf += received
    head, _, body = buf.partition(b"\r\n\r\n")
    length = 0
    for line in head.split(b"\r\n"):
        if line.lower().startswith(b"content-length:"):
            length = int(line.split(b":", 1)[1])
    while len(body) < length:
        body += conn.recv(65536)
    return True


def _origin(respond: Callable[[socket.socket], None]) -> Iterator[int]:
    """A local origin answering every request through `respond`; yields its port."""
    listener = socket.socket()
    listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    listener.bind(("127.0.0.1", 0))
    listener.listen(8)

    def serve(conn: socket.socket) -> None:
        with conn:
            if _read_request(conn):
                respond(conn)

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


def _sse_stream(events: tuple[dict, ...], *, gzip_encoded: bool = False) -> Callable[[socket.socket], None]:
    """Chunked SSE, one event every _SSE_GAP seconds.

    gzip_encoded is how the API sends every stream: the compressor is flushed
    after each event, which is what lets a client decode one on arrival.
    """

    def respond(conn: socket.socket) -> None:
        conn.sendall(
            b"HTTP/1.1 200 OK\r\n"
            b"Content-Type: text/event-stream\r\n"
            b"Transfer-Encoding: chunked\r\n"
            + (b"Content-Encoding: gzip\r\n" if gzip_encoded else b"")
            + b"Cache-Control: no-cache\r\n\r\n"
        )
        compressor = zlib.compressobj(wbits=31) if gzip_encoded else None
        for index, event in enumerate(events):
            if index:
                time.sleep(_SSE_GAP)
            payload = f"event: {event['type']}\ndata: {json.dumps(event, ensure_ascii=False)}\n\n".encode()
            if compressor:
                payload = compressor.compress(payload) + compressor.flush(zlib.Z_SYNC_FLUSH)
            conn.sendall(b"%x\r\n" % len(payload) + payload + b"\r\n")
        if compressor:
            trailer = compressor.flush()
            conn.sendall(b"%x\r\n" % len(trailer) + trailer + b"\r\n")
        conn.sendall(b"0\r\n\r\n")

    return respond


def _whole(status: str, body: bytes, *headers: str) -> Callable[[socket.socket], None]:
    """One response with a Content-Length body, sent in a single write."""
    lines = (f"HTTP/1.1 {status}", *headers, f"Content-Length: {len(body)}", "Connection: close")
    head = "".join(f"{line}\r\n" for line in lines).encode() + b"\r\n"

    def respond(conn: socket.socket) -> None:
        conn.sendall(head + body)

    return respond


@pytest.fixture(scope="module")
def sse_origin() -> Iterator[int]:
    yield from _origin(_sse_stream(_STREAM_EVENTS))


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


def _post_through_proxy(
    proxy_port: int,
    origin_port: int,
    session_id: str,
    extra_headers: tuple[tuple[str, str], ...] = (),
) -> list[tuple[float, bytes]]:
    """POST a conversation-shaped body and timestamp every arrival.

    The Host header is what the addon filters on (mitmproxy's
    Request.pretty_host prefers it over the destination address), so a local
    origin can stand in for api.anthropic.com without touching DNS.
    """
    body = json.dumps(
        {"model": "claude-stream-test", "messages": [{"role": "user", "content": "hi"}], "stream": True}
    ).encode()
    extra = "".join(f"{name}: {value}\r\n" for name, value in extra_headers)
    request = (
        f"POST http://127.0.0.1:{origin_port}/v1/messages?beta=true HTTP/1.1\r\n"
        f"Host: {proxy.TARGET_HOSTS[0]}\r\n"
        f"{proxy.SESSION_HEADER}: {session_id}\r\n"
        "Content-Type: application/json\r\n"
        f"Content-Length: {len(body)}\r\n"
        f"{extra}"
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
    # A clean completion writes nothing else. The client's end of stream follows
    # the response hook, so the hook is done by the time this runs.
    assert sorted(p.name for p in log_file.parent.iterdir()) == ["0001.json"]


@pytest.fixture(scope="module")
def error_origin() -> Iterator[int]:
    """An origin that refuses every call the way the API refuses one -- br-encoded,
    as the API sends every JSON body."""
    body = json.dumps(
        {"type": "error", "error": {"type": "rate_limit_error", "message": "requires usage credits"}}
    ).encode()
    yield from _origin(
        _whole(
            "429 Too Many Requests",
            brotli.compress(body),
            "Content-Type: application/json",
            "Content-Encoding: br",
        )
    )


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


# --- The HTTP envelope ---
#
# anthropic-beta varies per request inside one session -- 8 entries measured on
# an auxiliary call against 14 on the main one, cc 2.1.269 -- so nothing else on
# disk implies it and a capture without it cannot be re-sent.


def _capture_with_headers(proxy_port, origin_port, home, headers):
    session_id = str(uuid.uuid4())
    _post_through_proxy(proxy_port, origin_port, session_id, headers)
    log_file = home / ".claude" / "requests-log" / session_id / "0001.json"
    deadline = time.monotonic() + 10
    while not log_file.exists() and time.monotonic() < deadline:
        time.sleep(0.1)
    assert log_file.exists(), f"no capture written to {log_file}"
    return json.loads(log_file.read_text())


BETAS = "claude-code-20250219,oauth-2025-04-20,effort-2025-11-24"


def test_the_beta_list_and_the_query_string_reach_the_capture(sse_origin, proxy_process) -> None:
    proxy_port, home = proxy_process
    entry = _capture_with_headers(
        proxy_port, sse_origin, home,
        (("anthropic-beta", BETAS), ("x-app", "cli"), ("anthropic-version", "2023-06-01")),
    )

    http = entry["http"]
    assert http["method"] == "POST"
    assert http["url"].endswith("/v1/messages?beta=true")
    sent = {name.lower(): value for name, value in http["request_headers"]}
    assert sent["anthropic-beta"] == BETAS
    assert sent["x-app"] == "cli"
    assert sent["anthropic-version"] == "2023-06-01"


def test_the_credential_becomes_a_slot_description_and_not_a_value(sse_origin, proxy_process) -> None:
    """94,820 captures sit unencrypted under $HOME; none needs the secret."""
    proxy_port, home = proxy_process
    entry = _capture_with_headers(
        proxy_port, sse_origin, home,
        (("Authorization", "Bearer sk-secret-token-value"), ("x-api-key", "also-secret")),
    )

    http = entry["http"]
    names = {name.lower() for name, _ in http["request_headers"]}
    assert "authorization" not in names
    assert "x-api-key" not in names
    assert http["credential"] == {
        "header": "Authorization", "scheme": "Bearer", "length": len("Bearer sk-secret-token-value"),
    }
    assert "sk-secret-token-value" not in json.dumps(entry)


def test_a_repeated_header_keeps_both_values_and_the_send_order(sse_origin, proxy_process) -> None:
    """dict() would join these with ", "; pairs keep them separable."""
    proxy_port, home = proxy_process
    entry = _capture_with_headers(
        proxy_port, sse_origin, home,
        (("X-Repeat", "first"), ("X-Repeat", "second")),
    )

    repeats = [v for name, v in entry["http"]["request_headers"] if name.lower() == "x-repeat"]
    assert repeats == ["first", "second"]


def test_a_successful_call_records_its_status_and_response_headers(sse_origin, proxy_process) -> None:
    """Only a non-200 recorded a status before; error.status was the sole record."""
    proxy_port, home = proxy_process
    entry = _capture_with_headers(proxy_port, sse_origin, home, ())

    assert entry["http"]["response"]["status"] == 200
    resp = {name.lower() for name, _ in entry["http"]["response"]["headers"]}
    assert "content-type" in resp


def test_a_refused_call_records_the_http_region_too(error_origin, proxy_process) -> None:
    proxy_port, home = proxy_process
    entry = _capture_with_headers(
        proxy_port, error_origin, home, (("anthropic-beta", BETAS),),
    )

    assert entry["http"]["response"]["status"] == 429
    assert entry["error"]["status"] == 429
    sent = {name.lower(): value for name, value in entry["http"]["request_headers"]}
    assert sent["anthropic-beta"] == BETAS


# --- Failed-call detail log (NNNN.detail.json), end to end ---
#
# The reassembled NNNN.json keeps the message, not the stream it arrived as.
# These drive a real mitmdump, with origins encoding their bodies the way the API
# does, so the decoded bytes, the per-read timing and the sibling filename are
# pinned on the wire.

_REFUSAL_EVENTS = (
    {
        "type": "message_start",
        "message": {
            "id": "msg_refused",
            "model": "claude-stream-test",
            "role": "assistant",
            "usage": {"input_tokens": 3},
        },
    },
    {"type": "ping"},
    {"type": "content_block_start", "index": 0,
     "content_block": {"type": "thinking", "thinking": "", "signature": ""}},
    {"type": "content_block_delta", "index": 0,
     "delta": {"type": "thinking_delta", "thinking": "partial reasoning — cut short"}},
    {
        "type": "message_delta",
        "delta": {
            "stop_reason": "refusal",
            "stop_details": {
                "type": "refusal",
                "category": "reasoning_extraction",
                "explanation": "blocked by ToS",
            },
        },
        "usage": {"output_tokens": 99},
    },
)


@pytest.fixture(scope="module")
def refusal_origin() -> Iterator[int]:
    """A gzip SSE stream that ends in stop_reason: refusal, one event per gap."""
    yield from _origin(_sse_stream(_REFUSAL_EVENTS, gzip_encoded=True))


def _wait_for(path: Path, timeout: float = 10) -> None:
    deadline = time.monotonic() + timeout
    while not path.exists() and time.monotonic() < deadline:
        time.sleep(0.1)
    assert path.exists(), f"never written: {path}"


def test_a_refusal_writes_a_detail_log_with_the_decoded_stream_and_its_timing(
    refusal_origin, proxy_process
) -> None:
    proxy_port, home = proxy_process
    session_id = str(uuid.uuid4())
    _post_through_proxy(proxy_port, refusal_origin, session_id, (("x-api-key", "sk-ant-SECRET"),))

    session_dir = home / ".claude" / "requests-log" / session_id
    _wait_for(session_dir / "0001.detail.json")

    normal = json.loads((session_dir / "0001.json").read_text())
    assert normal["response"]["stop_reason"] == "refusal"

    detail_text = (session_dir / "0001.detail.json").read_text()
    assert "sk-ant-SECRET" not in detail_text
    detail = json.loads(detail_text)
    assert detail["detail_for"] == "0001.json"
    assert detail["trigger"]["kind"] == "refusal"
    assert detail["trigger"]["stop_details"]["category"] == "reasoning_extraction"
    assert detail["response"] == normal["response"]

    # gzip undone, every event kept in arrival order -- the ping included, which
    # the reassembled message drops by design.
    raw = detail["raw_response"]
    assert "event: ping" in raw
    assert "ping" not in json.dumps(normal["response"])
    assert "partial reasoning — cut short" in raw
    assert "\ufffd" not in raw

    chunks = detail["chunks"]
    assert "".join(c["text"] for c in chunks) == raw
    assert all(set(c) == {"offset_ms", "bytes", "text"} and c["bytes"] > 0 for c in chunks)
    offsets = [c["offset_ms"] for c in chunks]
    assert offsets == sorted(offsets)

    def arrived(needle: str) -> int:
        return next(c["offset_ms"] for c in chunks if needle in c["text"])

    # Each event was its own read, so the stop is stamped a gap or more after
    # the start; a buffering relay would stamp both at the same instant.
    assert arrived("event: message_delta") - arrived("event: message_start") >= _SSE_GAP * 1000


@pytest.fixture(scope="module")
def unparseable_origin() -> Iterator[int]:
    """A 200 whose body carries no SSE `data:` event, so reassembly raises."""
    yield from _origin(
        _whole("200 OK", b"event: ping\nnot an sse data line at all\n", "Content-Type: text/event-stream")
    )


def test_an_unparseable_stream_keeps_its_raw_bytes_in_a_detail_log(
    unparseable_origin, proxy_process
) -> None:
    proxy_port, home = proxy_process
    session_id = str(uuid.uuid4())
    _post_through_proxy(proxy_port, unparseable_origin, session_id)

    session_dir = home / ".claude" / "requests-log" / session_id
    _wait_for(session_dir / "0001.detail.json")

    normal = json.loads((session_dir / "0001.json").read_text())
    assert "response" not in normal
    assert normal["error"] == {"parse_error": "no SSE data events in a streamed response"}

    detail = json.loads((session_dir / "0001.detail.json").read_text())
    assert detail["trigger"] == {
        "kind": "parse_error", "message": "no SSE data events in a streamed response",
    }
    assert detail["response"] is None
    assert detail["raw_response"] == "event: ping\nnot an sse data line at all\n"


# A body labelled gzip that is not gzip: mitmproxy cannot undo it either.
_MISLABELLED = b'event: ping\ndata: {"type": "ping"}\n\n'


@pytest.fixture(scope="module")
def mislabelled_origin() -> Iterator[int]:
    yield from _origin(
        _whole("200 OK", _MISLABELLED, "Content-Type: text/event-stream", "Content-Encoding: gzip")
    )


def test_a_body_whose_encoding_will_not_undo_keeps_its_wire_bytes(
    mislabelled_origin, proxy_process
) -> None:
    proxy_port, home = proxy_process
    session_id = str(uuid.uuid4())
    _post_through_proxy(proxy_port, mislabelled_origin, session_id)

    session_dir = home / ".claude" / "requests-log" / session_id
    _wait_for(session_dir / "0001.detail.json")

    normal = json.loads((session_dir / "0001.json").read_text())
    assert "incorrect header check" in normal["error"]["parse_error"]

    detail = json.loads((session_dir / "0001.detail.json").read_text())
    assert detail["trigger"]["kind"] == "parse_error"
    assert detail["raw_response"] is None
    assert base64.b64decode(detail["raw_response_base64"]) == _MISLABELLED
    assert "incorrect header check" in detail["decode_error"]
    assert [set(c) for c in detail["chunks"]] == [{"offset_ms", "bytes"}] * len(detail["chunks"])
    assert sum(c["bytes"] for c in detail["chunks"]) == len(_MISLABELLED)
    errors = (home / ".claude" / "requests-log" / "_errors" / "errors.log").read_text()
    assert "decode-detail" in errors


def test_a_non_200_also_writes_a_detail_log(error_origin, proxy_process) -> None:
    proxy_port, home = proxy_process
    session_id = str(uuid.uuid4())
    _post_through_proxy(proxy_port, error_origin, session_id)

    session_dir = home / ".claude" / "requests-log" / session_id
    _wait_for(session_dir / "0001.detail.json")

    detail = json.loads((session_dir / "0001.detail.json").read_text())
    assert detail["trigger"] == {
        "kind": "http_error", "status": 429, "statusText": "Too Many Requests",
    }
    assert detail["http"]["response"]["status"] == 429
    assert detail["response"] is None
    # br undone: the API's JSON, not its compressed bytes.
    assert json.loads(detail["raw_response"])["error"]["message"] == "requires usage credits"
