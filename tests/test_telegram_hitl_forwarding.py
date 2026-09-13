"""Tests for the forwarder: it passes calls through and interprets nothing."""

import json
import socket
import threading
import time
from pathlib import Path
from types import SimpleNamespace

import pytest

from claude_config.telegram_hitl import server as server_module
from claude_config.telegram_hitl.log import ChannelLog
from claude_config.telegram_hitl.server import DENIED, ProxyServer

TOKEN = "42:test-token"


def _records(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines()]


def _connect(socket_path: Path) -> socket.socket:
    """A raw connection, for the tests that send bytes http.client would not."""
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sock.settimeout(10)
    sock.connect(str(socket_path))
    return sock


def _faults(path: Path) -> list[dict]:
    return [r for r in _records(path) if r["kind"] == "fault"]


@pytest.fixture
def proxy(tmp_path, fake_telegram):
    """The forwarder in-process, pointed at the fake Bot API."""
    log_path = tmp_path / "channel.jsonl"
    log = ChannelLog(log_path)
    socket_path = tmp_path / "proxy.sock"
    server = ProxyServer(socket_path, log, api_base=fake_telegram.base, token=TOKEN)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    yield SimpleNamespace(socket=socket_path, log_path=log_path, fake=fake_telegram)
    server.shutdown()
    server.server_close()
    log.close()


def test_a_send_reaches_telegram_unchanged(proxy, unix_call) -> None:
    proxy.fake.queue(200, {"ok": True, "result": {"message_id": 7}})
    body = json.dumps({"chat_id": -100, "text": "why?"}).encode()

    status, answer = unix_call(proxy.socket, "sendMessage", data=body,
                               headers={"Content-Type": "application/json"})

    assert (status, json.loads(answer)) == (200, {"ok": True, "result": {"message_id": 7}})
    seen = proxy.fake.requests[0]
    assert seen.path == f"/bot{TOKEN}/sendMessage"
    assert seen.verb == "POST"
    assert seen.body == body


def test_an_error_reaches_the_caller_verbatim(proxy, unix_call) -> None:
    """Limits are diagnosed, not absorbed: retry_after must survive the hop."""
    flood = {"ok": False, "error_code": 429, "description": "Too Many Requests",
             "parameters": {"retry_after": 17}}
    proxy.fake.queue(429, flood)

    status, answer = unix_call(proxy.socket, "sendMessage", data=b"{}",
                               headers={"Content-Type": "application/json"})

    assert status == 429
    assert json.loads(answer) == flood


def test_a_get_is_forwarded_as_a_get_with_its_query(proxy, unix_call) -> None:
    proxy.fake.queue(200, {"ok": True, "result": {"username": "claude_channel_bot"}})

    status, answer = unix_call(proxy.socket, "getChat?chat_id=-100")

    assert status == 200
    assert json.loads(answer)["result"]["username"] == "claude_channel_bot"
    assert proxy.fake.requests[0].verb == "GET"
    assert proxy.fake.requests[0].path == f"/bot{TOKEN}/getChat?chat_id=-100"


@pytest.mark.parametrize("method", ["getUpdates", "getupdates", "setWebhook",
                                    "deleteWebhook", "close", "logOut"])
def test_a_denied_method_never_reaches_telegram(proxy, unix_call, method) -> None:
    status, answer = unix_call(proxy.socket, method, data=b"{}",
                               headers={"Content-Type": "application/json"})

    assert status == 403
    envelope = json.loads(answer)
    assert envelope["ok"] is False
    assert "telegram-hitl proxy" in envelope["description"]
    assert proxy.fake.requests == []
    assert _records(proxy.log_path)[0]["kind"] == "denied"


@pytest.mark.parametrize("spelling", ["getUpdates/", "get%55pdates", "%67etUpdates",
                                     "sendMessage/../getUpdates"])
def test_a_denied_method_cannot_be_reached_by_respelling_it(proxy, unix_call,
                                                            spelling) -> None:
    """Measured before the shape check existed: every one of these passed the
    denylist and reached Telegram with the denied name intact. Stealing the
    update cursor is the worst thing a caller can do to this system."""
    status, answer = unix_call(proxy.socket, spelling, data=b"{}",
                               headers={"Content-Type": "application/json"})

    assert status == 400
    assert "not a Bot API method name" in json.loads(answer)["description"]
    assert proxy.fake.requests == []


def test_a_chunked_body_is_refused_rather_than_forwarded_empty(proxy) -> None:
    """A chunked body carries no Content-Length, so it reads as empty. Forwarding
    it would be a send with no fields that the agent believes it made."""
    payload = b'{"chat_id":-100,"text":"a chunked message"}'
    sock = _connect(proxy.socket)
    sock.sendall(b"POST /sendMessage HTTP/1.1\r\nHost: proxy\r\n"
                 b"Content-Type: application/json\r\nTransfer-Encoding: chunked\r\n\r\n"
                 + f"{len(payload):x}".encode() + b"\r\n" + payload + b"\r\n0\r\n\r\n")
    answer = sock.recv(4096)
    sock.close()

    assert b"411" in answer.split(b"\r\n")[0]
    assert proxy.fake.requests == []
    assert _records(proxy.log_path)[0]["kind"] == "denied"


def test_a_handler_that_raises_is_recorded_rather_than_lost(proxy) -> None:
    """A raising handler answers nobody and this server's stderr is read by
    nobody, so the fault has to reach the log to exist at all."""
    sock = _connect(proxy.socket)
    sock.sendall(b"POST /sendMessage HTTP/1.1\r\nHost: proxy\r\n"
                 b"Content-Type: application/json\r\nContent-Length: not-a-number\r\n\r\n")
    sock.close()

    deadline = time.monotonic() + 10
    while not _faults(proxy.log_path) and time.monotonic() < deadline:
        time.sleep(0.05)
    assert _faults(proxy.log_path)[0]["signature"] == "handler:ValueError"


def test_every_denied_method_states_why(proxy) -> None:
    assert set(DENIED) == {"getupdates", "setwebhook", "deletewebhook", "close", "logout"}
    assert all(reason for reason in DENIED.values())


def test_a_call_is_logged_with_its_response_and_its_caller(proxy, unix_call) -> None:
    proxy.fake.queue(200, {"ok": True, "result": {"message_id": 7}})

    unix_call(proxy.socket, "sendMessage",
              data=json.dumps({"chat_id": -100, "text": "why?"}).encode(),
              headers={"Content-Type": "application/json", "X-Session-Id": "sess-1"})

    record = _records(proxy.log_path)[0]
    assert record["kind"] == "outbound"
    assert record["method"] == "sendMessage"
    assert record["session"] == "sess-1"
    assert record["params"] == {"chat_id": -100, "text": "why?"}
    assert record["status"] == 200
    assert record["response"] == {"ok": True, "result": {"message_id": 7}}
    assert isinstance(record["elapsed_ms"], int)


def test_a_non_json_body_is_logged_as_text(proxy, unix_call) -> None:
    unix_call(proxy.socket, "sendMessage", data=b"chat_id=-100&text=why",
              headers={"Content-Type": "application/x-www-form-urlencoded"})

    assert _records(proxy.log_path)[0]["params"] == "chat_id=-100&text=why"


def test_an_unreachable_telegram_is_reported_and_logged(tmp_path, unix_call) -> None:
    """The channel being down must look different from a human being slow."""
    log_path = tmp_path / "channel.jsonl"
    log = ChannelLog(log_path)
    server = ProxyServer(tmp_path / "proxy.sock", log,
                         api_base="http://127.0.0.1:1", token=TOKEN)
    threading.Thread(target=server.serve_forever, daemon=True).start()

    status, answer = unix_call(tmp_path / "proxy.sock", "sendMessage",
                               data=b"{}", headers={"Content-Type": "application/json"})

    server.shutdown()
    server.server_close()
    log.close()
    assert status == 502
    assert "telegram-hitl proxy" in json.loads(answer)["description"]
    fault = _records(log_path)[0]
    assert (fault["kind"], fault["source"], fault["state"]) == ("fault", "forward", "failing")


def test_an_upstream_that_never_answers_is_reported_and_logged(tmp_path, unix_call,
                                                              monkeypatch) -> None:
    """A hang is the likeliest outage shape and the one that used to leave no
    record at all: what it raises is not a URLError until upstream.call makes
    it one, so nothing caught it and the caller got a dropped connection."""
    monkeypatch.setattr(server_module, "FORWARD_TIMEOUT", 0.5)
    listener = socket.socket()
    listener.bind(("127.0.0.1", 0))
    listener.listen(1)
    held: list[socket.socket] = []
    threading.Thread(target=lambda: held.append(listener.accept()[0]), daemon=True).start()

    log_path = tmp_path / "channel.jsonl"
    log = ChannelLog(log_path)
    server = ProxyServer(tmp_path / "proxy.sock", log, token=TOKEN,
                         api_base=f"http://127.0.0.1:{listener.getsockname()[1]}")
    threading.Thread(target=server.serve_forever, daemon=True).start()

    status, answer = unix_call(tmp_path / "proxy.sock", "sendMessage",
                               data=b"{}", headers={"Content-Type": "application/json"})

    server.shutdown()
    server.server_close()
    log.close()
    listener.close()
    assert status == 502
    assert "telegram-hitl proxy" in json.loads(answer)["description"]
    assert _faults(log_path)[0]["source"] == "forward"


SENDERS = 32
"""Enough to overrun socketserver's default backlog of 5 every time.

At 10 senders the default failed 2 runs in 15 — a guard that mostly does not
fire. At 32 it fails every run and passes on the 128 `ProxyServer` configures
(measured 2026-09-13: 5/5 failures at 5, 0/15 at 128). The fake upstream in
`conftest.py` carries the same raised backlog, or its own refusals arrive here
as the proxy's 502s.
"""


def test_concurrent_senders_all_succeed_and_are_all_logged(proxy, unix_call) -> None:
    """Outbound needs no coordination — the measurement the design rests on."""
    results: list[int] = []
    lock = threading.Lock()

    def send(n: int) -> None:
        status, _ = unix_call(proxy.socket, "sendMessage",
                              data=json.dumps({"text": f"q{n}"}).encode(),
                              headers={"Content-Type": "application/json"})
        with lock:
            results.append(status)

    threads = [threading.Thread(target=send, args=(n,)) for n in range(SENDERS)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert results == [200] * SENDERS
    records = _records(proxy.log_path)
    assert len(records) == SENDERS
    assert {r["params"]["text"] for r in records} == {f"q{n}" for n in range(SENDERS)}


def test_the_forwarder_serves_on_a_unix_socket(tmp_path, fake_telegram, unix_call) -> None:
    """A path names one endpoint everywhere. A port number does not: it resolves
    to a different socket in every network namespace that reads it, so the file
    recording it cannot say what a reader is meant to dial."""
    log = ChannelLog(tmp_path / "channel.jsonl")
    socket_path = tmp_path / "proxy.sock"
    server = ProxyServer(socket_path, log, api_base=fake_telegram.base, token=TOKEN)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    fake_telegram.queue(200, {"ok": True, "result": {"message_id": 7}})

    status, answer = unix_call(socket_path, "sendMessage", data=b'{"chat_id":-100}',
                               headers={"Content-Type": "application/json"})

    server.shutdown()
    server.server_close()
    log.close()
    assert (status, json.loads(answer)["result"]) == (200, {"message_id": 7})
    assert fake_telegram.requests[0].path == f"/bot{TOKEN}/sendMessage"


def test_a_socket_path_over_the_kernel_limit_names_the_limit(tmp_path) -> None:
    """The kernel caps sun_path at 108 bytes, well under PATH_MAX, so a state
    directory the log opens fine is a socket path that cannot bind. Python
    reports that as a bare `AF_UNIX path too long`, which names neither the path
    nor the budget."""
    deep = tmp_path / ("d" * 80) / ("e" * 80)
    deep.mkdir(parents=True)
    log = ChannelLog(tmp_path / "channel.jsonl")

    with pytest.raises(OSError, match="108"):
        ProxyServer(deep / "proxy.sock", log, api_base="http://127.0.0.1:1", token=TOKEN)
    log.close()
