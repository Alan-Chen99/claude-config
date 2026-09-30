"""cc-replay turns a capture into an editable request and sends it back.

The extract/send pair exists so a what-if is a file you edit rather than a flag
you remember, and so a replay's result renders under the same front-end as the
capture it came from.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from claude_config.cc_replay.extract import extract
from claude_config.cc_replay.proxy_module import load_proxy

HTTP = {
    "method": "POST",
    "url": "https://api.anthropic.com/v1/messages?beta=true",
    "http_version": "HTTP/1.1",
    "request_headers": [
        ["Accept", "application/json"],
        ["anthropic-beta", "claude-code-20250219,effort-2025-11-24"],
        ["Content-Length", "4145"],
        ["Host", "api.anthropic.com"],
        ["x-client-request-id", "7fa860c6-4611-456e-b4ed-415f87619442"],
        ["X-Stainless-Retry-Count", "2"],
        ["X-Claude-Code-Session-Id", "ea529de9-61c3-422b-8868-b008a66ded9d"],
    ],
    "credential": {"header": "Authorization", "scheme": "Bearer", "length": 115},
    "response": {
        "status": 200, "reason": "OK",
        "headers": [["request-id", "req_011CfYdgBnuh"]],
    },
}


def capture(**over) -> dict:
    base = {
        "timestamp": "2026-09-29T23:54:47+00:00",
        "duration_ms": 2100,
        "session": {"session_id": "ea529de9-61c3-422b-8868-b008a66ded9d"},
        "streaming": True,
        "request": {
            "model": "claude-opus-5",
            "messages": [{"role": "user", "content": "hi"}],
            "stream": True,
        },
        "response": {"model": "claude-opus-5", "usage": {"input_tokens": 9, "output_tokens": 3}},
        "http": HTTP,
    }
    base.update(over)
    return base


def write_capture(tmp_path: Path, cap: dict) -> Path:
    path = tmp_path / "0007.json"
    path.write_text(json.dumps(cap))
    return path


def test_the_addon_loader_finds_parse_sse_stream() -> None:
    """The dependency runs package -> addon; proxy.py imports nothing."""
    assert callable(load_proxy().parse_sse_stream)


def test_extract_writes_the_body_the_call_and_what_it_answered(tmp_path) -> None:
    out = tmp_path / "w1"
    extract(write_capture(tmp_path, capture()), out)

    body = json.loads((out / "request.json").read_text())
    http = json.loads((out / "http.json").read_text())
    meta = json.loads((out / "meta.json").read_text())

    assert body["model"] == "claude-opus-5"
    assert http["headers_source"] == "captured"
    assert http["url"].endswith("?beta=true")
    assert ["anthropic-beta", "claude-code-20250219,effort-2025-11-24"] in http["request_headers"]
    # The original response's own headers belong to the original, not to what
    # is about to be sent.
    assert "response" not in http
    assert meta["request_id"] == "req_011CfYdgBnuh"
    assert meta["status"] == 200
    assert meta["usage"] == {"input_tokens": 9, "output_tokens": 3}
    assert meta["source"].endswith("0007.json")


def test_extract_refuses_to_overwrite_a_directory_with_work_in_it(tmp_path) -> None:
    out = tmp_path / "w1"
    out.mkdir()
    (out / "request.json").write_text("{}")

    with pytest.raises(FileExistsError):
        extract(write_capture(tmp_path, capture()), out)

    extract(write_capture(tmp_path, capture()), out, force=True)
    assert json.loads((out / "request.json").read_text())["model"] == "claude-opus-5"


def test_a_capture_with_no_http_region_is_marked_synthesized(tmp_path) -> None:
    """The betas are unrecoverable; saying so is the whole point of the mark."""
    cap = capture()
    del cap["http"]
    out = tmp_path / "old"
    extract(write_capture(tmp_path, cap), out)

    http = json.loads((out / "http.json").read_text())
    assert http["headers_source"] == "synthesized"
    assert http["url"] == "https://api.anthropic.com/v1/messages?beta=true"
    assert not any(name.lower() == "anthropic-beta" for name, _ in http["request_headers"])


@pytest.mark.parametrize(
    ("model", "host"),
    [("k3", "api.kimi.ai"), ("glm-5.3", "api.z.ai"), ("claude-opus-5", "api.anthropic.com")],
)
def test_a_synthesized_url_picks_its_host_off_the_model_id(tmp_path, model, host) -> None:
    cap = capture()
    del cap["http"]
    cap["request"]["model"] = model
    out = tmp_path / model
    extract(write_capture(tmp_path, cap), out)

    assert json.loads((out / "http.json").read_text())["url"] == f"https://{host}/v1/messages?beta=true"


# ── Credentials ─────────────────────────────────────────────────────────────
#
# A capture never carries one. Every resolution names its source, because an
# API key and an OAuth bearer are not the same caller: whether a beta such as
# claude-code-20250219 is gated to the OAuth path is unverified, so a replay
# that diverges from its capture must be able to rule the credential in or out.

import time as _time

from claude_config.cc_replay import credentials as creds


def _store(tmp_path, token="oauth-token-value", expires_in=3600.0):
    path = tmp_path / ".credentials.json"
    path.write_text(json.dumps({
        "claudeAiOauth": {
            "accessToken": token,
            "expiresAt": int((_time.time() + expires_in) * 1000),
        }
    }))
    return path


def test_the_first_party_host_resolves_the_oauth_store_first(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(creds, "OAUTH_STORE", _store(tmp_path))
    monkeypatch.setenv("ANTHROPIC_API_KEY", "an-api-key")

    cred = creds.resolve("https://api.anthropic.com/v1/messages?beta=true")
    assert cred is not None
    assert cred.header == "Authorization"
    assert cred.value == "Bearer oauth-token-value"
    assert "claudeAiOauth" in cred.source


def test_an_api_key_fills_in_when_the_store_has_no_token(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(creds, "OAUTH_STORE", tmp_path / "absent.json")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "an-api-key")

    cred = creds.resolve("https://api.anthropic.com/v1/messages")
    assert cred is not None
    assert (cred.header, cred.value) == ("x-api-key", "an-api-key")
    assert cred.source == "$ANTHROPIC_API_KEY"


def test_an_expired_oauth_token_is_refused_by_name(tmp_path, monkeypatch) -> None:
    """A 401 from a stale token reads as an API fault; this does not."""
    monkeypatch.setattr(creds, "OAUTH_STORE", _store(tmp_path, expires_in=-60.0))
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    with pytest.raises(RuntimeError, match="expired"):
        creds.resolve("https://api.anthropic.com/v1/messages")


@pytest.mark.parametrize(
    ("host", "var"),
    [("api.kimi.ai", "KIMI_API_KEY"), ("api.z.ai", "ZAI_API_KEY")],
)
def test_each_provider_host_reads_its_own_key(monkeypatch, host, var) -> None:
    monkeypatch.setenv(var, "provider-key")
    cred = creds.resolve(f"https://{host}/v1/messages")
    assert cred is not None
    assert (cred.header, cred.value, cred.source) == ("Authorization", "Bearer provider-key", f"${var}")


def test_an_unknown_host_is_refused_rather_than_sent_uncredentialed() -> None:
    with pytest.raises(RuntimeError, match="127.0.0.1"):
        creds.resolve("http://127.0.0.1:8080/v1/messages")


def test_no_credential_and_an_explicit_env_var_both_override_the_table(monkeypatch) -> None:
    assert creds.resolve("http://127.0.0.1:8080/v1/messages", none=True) is None

    monkeypatch.setenv("MY_TOKEN", "t")
    cred = creds.resolve("http://127.0.0.1:8080/v1/messages", env_var="MY_TOKEN")
    assert cred is not None
    assert cred.value == "Bearer t"

    monkeypatch.delenv("MY_TOKEN")
    with pytest.raises(RuntimeError, match="MY_TOKEN"):
        creds.resolve("http://127.0.0.1:8080/v1/messages", env_var="MY_TOKEN")


def test_every_source_coming_up_empty_names_what_was_tried(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(creds, "OAUTH_STORE", tmp_path / "absent.json")
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    with pytest.raises(RuntimeError, match=r"ANTHROPIC_API_KEY"):
        creds.resolve("https://api.anthropic.com/v1/messages")


# ── Sending ─────────────────────────────────────────────────────────────────

import socket
import threading

from claude_config.cc_replay.send import DEVIATIONS, outgoing_headers, send

SEEN: list[list[str]] = []

_EVENTS = (
    {"type": "message_start", "message": {"id": "msg_replay", "model": "claude-replayed",
                                          "role": "assistant", "usage": {"input_tokens": 5}}},
    {"type": "content_block_start", "index": 0, "content_block": {"type": "text", "text": ""}},
    {"type": "content_block_delta", "index": 0,
     "delta": {"type": "text_delta", "text": "replayed"}},
    {"type": "message_delta", "delta": {"stop_reason": "end_turn"}, "usage": {"output_tokens": 2}},
)


def _serve(conn: socket.socket, status: bytes, payload: bytes | None) -> None:
    buf = b""
    while b"\r\n\r\n" not in buf:
        received = conn.recv(65536)
        if not received:
            conn.close()
            return
        buf += received
    head, _, rest = buf.partition(b"\r\n\r\n")
    lines = head.decode().split("\r\n")
    SEEN.append(lines)
    length = next(
        (int(line.split(":", 1)[1]) for line in lines
         if line.lower().startswith("content-length:")), 0
    )
    while len(rest) < length:
        rest += conn.recv(65536)

    if payload is not None:
        conn.sendall(
            status + b"Content-Type: application/json\r\n"
            b"Content-Length: %d\r\nConnection: close\r\n\r\n" % len(payload) + payload
        )
    else:
        conn.sendall(
            status + b"Content-Type: text/event-stream\r\n"
            b"Transfer-Encoding: chunked\r\nCache-Control: no-cache\r\n"
            b"request-id: req_replayed\r\n\r\n"
        )
        for event in _EVENTS:
            chunk = f"data: {json.dumps(event)}\n\n".encode()
            conn.sendall(b"%x\r\n" % len(chunk) + chunk + b"\r\n")
        conn.sendall(b"0\r\n\r\n")
    conn.close()


@pytest.fixture
def origin():
    """A local origin answering with SSE, or with whatever `respond_with` sets."""
    state: dict = {"status": b"HTTP/1.1 200 OK\r\n", "payload": None}
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
            threading.Thread(
                target=_serve, args=(conn, state["status"], state["payload"]), daemon=True
            ).start()

    threading.Thread(target=accept_loop, daemon=True).start()
    SEEN.clear()
    yield listener.getsockname()[1], state
    listener.close()


def test_the_five_deviating_headers_deviate_and_nothing_else_changes() -> None:
    sent = outgoing_headers(HTTP["request_headers"])
    names = [name.lower() for name, _ in sent]

    assert "content-length" not in names
    assert "host" not in names
    assert "connection" not in names
    values = dict(sent)
    assert values["X-Stainless-Retry-Count"] == "0"
    assert values["x-client-request-id"] != "7fa860c6-4611-456e-b4ed-415f87619442"
    # Everything else, casing and order intact.
    assert [name for name, _ in sent] == [
        "Accept", "anthropic-beta", "x-client-request-id",
        "X-Stainless-Retry-Count", "X-Claude-Code-Session-Id",
    ]
    assert values["anthropic-beta"] == "claude-code-20250219,effort-2025-11-24"
    # The session id reached Anthropic on the original call.
    assert values["X-Claude-Code-Session-Id"] == "ea529de9-61c3-422b-8868-b008a66ded9d"
    assert set(DEVIATIONS) == {
        "x-client-request-id", "x-stainless-retry-count",
        "content-length", "host", "connection",
    }


def test_a_send_round_trips_and_the_result_renders_as_a_capture(tmp_path, origin) -> None:
    from claude_config.cc_pretty_intercept.main import main as render_main

    port, _ = origin
    out = tmp_path / "w1"
    extract(write_capture(tmp_path, capture()), out)

    result = send(out, url=f"http://127.0.0.1:{port}/v1/messages?beta=true",
                  credential=None)

    entry = json.loads(result.read_text())
    assert entry["response"]["id"] == "msg_replay"
    assert entry["response"]["content"] == [{"type": "text", "text": "replayed"}]
    assert entry["http"]["response"]["status"] == 200
    assert entry["replay"]["headers_source"] == "captured"
    assert entry["replay"]["source"].endswith("0007.json")
    assert set(entry["replay"]["deviations"]) == set(DEVIATIONS)
    # The raw stream, kept because comparing streams is what a faithful
    # re-send is for.
    assert "data: " in result.with_suffix(".sse").read_text()

    # The result is a capture, so the capture front-end renders it.
    render_main([str(result), "--show-http"])


def test_the_origin_receives_the_captured_betas_and_a_fresh_request_id(tmp_path, origin) -> None:
    port, _ = origin
    out = tmp_path / "w1"
    extract(write_capture(tmp_path, capture()), out)
    send(out, url=f"http://127.0.0.1:{port}/v1/messages", credential=None)

    received = {
        line.split(":", 1)[0].lower(): line.split(":", 1)[1].strip()
        for line in SEEN[0][1:] if ":" in line
    }
    assert received["anthropic-beta"] == "claude-code-20250219,effort-2025-11-24"
    assert received["x-stainless-retry-count"] == "0"
    assert received["x-client-request-id"] != "7fa860c6-4611-456e-b4ed-415f87619442"


def test_a_second_send_does_not_overwrite_the_first_result(tmp_path, origin) -> None:
    port, _ = origin
    out = tmp_path / "w1"
    extract(write_capture(tmp_path, capture()), out)

    first = send(out, url=f"http://127.0.0.1:{port}/v1/messages", credential=None)
    second = send(out, url=f"http://127.0.0.1:{port}/v1/messages", credential=None)

    assert first.name == "result-0001.json"
    assert second.name == "result-0002.json"


def test_a_refused_replay_records_the_api_s_own_reason(tmp_path, origin) -> None:
    port, state = origin
    state["status"] = b"HTTP/1.1 429 Too Many Requests\r\n"
    state["payload"] = json.dumps(
        {"type": "error", "error": {"type": "rate_limit_error", "message": "slow down"}}
    ).encode()

    out = tmp_path / "w1"
    extract(write_capture(tmp_path, capture()), out)
    result = send(out, url=f"http://127.0.0.1:{port}/v1/messages", credential=None)

    entry = json.loads(result.read_text())
    assert "response" not in entry
    assert entry["error"] == {
        "status": 429, "statusText": "Too Many Requests",
        "type": "rate_limit_error", "message": "slow down",
    }


def test_send_refuses_synthesized_headers_until_told_to_accept_them(tmp_path, origin) -> None:
    """A re-send missing the original betas is a different call."""
    port, _ = origin
    cap = capture()
    del cap["http"]
    out = tmp_path / "old"
    extract(write_capture(tmp_path, cap), out)

    with pytest.raises(RuntimeError, match="synthesized"):
        send(out, url=f"http://127.0.0.1:{port}/v1/messages", credential=None)

    result = send(out, url=f"http://127.0.0.1:{port}/v1/messages", credential=None,
                  accept_synthesized=True)
    assert json.loads(result.read_text())["replay"]["headers_source"] == "synthesized"


def test_the_credential_is_sent_but_never_written_to_the_result(tmp_path, origin) -> None:
    port, _ = origin
    out = tmp_path / "w1"
    extract(write_capture(tmp_path, capture()), out)

    result = send(
        out, url=f"http://127.0.0.1:{port}/v1/messages",
        credential=creds.Credential("Authorization", "Bearer super-secret", "$TEST"),
    )

    received = {line.split(":", 1)[0].lower() for line in SEEN[0][1:] if ":" in line}
    assert "authorization" in received
    assert "super-secret" not in result.read_text()
    assert json.loads(result.read_text())["replay"]["credential"] == "$TEST"


def test_a_non_streaming_request_is_stored_verbatim(tmp_path, origin) -> None:
    port, state = origin
    state["payload"] = json.dumps(
        {"id": "msg_plain", "model": "m", "content": [{"type": "text", "text": "plain"}]}
    ).encode()

    cap = capture()
    cap["request"]["stream"] = False
    out = tmp_path / "w1"
    extract(write_capture(tmp_path, cap), out)
    result = send(out, url=f"http://127.0.0.1:{port}/v1/messages", credential=None)

    entry = json.loads(result.read_text())
    assert entry["streaming"] is False
    assert entry["response"]["id"] == "msg_plain"


def test_an_env_credential_can_take_the_api_key_header_shape(monkeypatch) -> None:
    """The two first-party credential shapes are not interchangeable.

    An OAuth token authenticates as `Authorization: Bearer`; an API key
    authenticates as `x-api-key`, unprefixed. Sending either on the other's
    header is an authentication failure, so the override that names the variable
    has to be able to name the header too.
    """
    monkeypatch.setenv("MY_KEY", "sk-ant-api03-xyz")

    bearer = creds.resolve("https://api.anthropic.com/v1/messages", env_var="MY_KEY")
    assert bearer is not None
    assert (bearer.header, bearer.value) == ("Authorization", "Bearer sk-ant-api03-xyz")

    key = creds.resolve(
        "https://api.anthropic.com/v1/messages",
        env_var="MY_KEY",
        env_header="x-api-key",
    )
    assert key is not None
    assert (key.header, key.value) == ("x-api-key", "sk-ant-api03-xyz")


# A 429 has two unrelated causes with opposite remedies, and the body says
# nothing: `{"type":"error","error":{"type":"rate_limit_error","message":"Error"}}`.
# The response headers separate them, so the summary reads them out.

from claude_config.cc_replay.main import rate_limit_note


def test_a_quota_429_names_the_organization_and_the_api_key_remedy() -> None:
    note = rate_limit_note(
        429,
        [
            ["x-should-retry", "true"],
            ["anthropic-organization-id", "29f2cf32-1268-49fe-8794-9032b532a49a"],
        ],
    )
    assert note is not None
    assert "29f2cf32-1268-49fe-8794-9032b532a49a" in note
    assert "--credential-header x-api-key" in note


def test_a_window_429_says_wait_instead_of_naming_a_credential() -> None:
    note = rate_limit_note(
        429,
        [
            ["anthropic-ratelimit-unified-5h-status", "rejected"],
            ["anthropic-ratelimit-unified-reset", "2026-09-30T02:00:00Z"],
        ],
    )
    assert note is not None
    assert "2026-09-30T02:00:00Z" in note
    assert "x-api-key" not in note


def test_a_status_that_is_not_429_gets_no_note() -> None:
    assert rate_limit_note(200, [["anthropic-organization-id", "x"]]) is None
    assert rate_limit_note(400, []) is None
