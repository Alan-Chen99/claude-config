"""Tests for the forwarder: it passes calls through and interprets nothing."""

import json
import threading
from pathlib import Path
from types import SimpleNamespace

import pytest

from claude_config.telegram_hitl.log import ChannelLog
from claude_config.telegram_hitl.server import DENIED, ProxyServer

TOKEN = "42:test-token"


def _records(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines()]


@pytest.fixture
def proxy(tmp_path, fake_telegram):
    """The forwarder in-process, pointed at the fake Bot API."""
    log_path = tmp_path / "channel.jsonl"
    log = ChannelLog(log_path)
    server = ProxyServer(("127.0.0.1", 0), log, api_base=fake_telegram.base, token=TOKEN)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    yield SimpleNamespace(base=f"http://127.0.0.1:{server.server_port}",
                          log_path=log_path, fake=fake_telegram)
    server.shutdown()
    server.server_close()
    log.close()


def test_a_send_reaches_telegram_unchanged(proxy, http_call) -> None:
    proxy.fake.queue(200, {"ok": True, "result": {"message_id": 7}})
    body = json.dumps({"chat_id": -100, "text": "why?"}).encode()

    status, answer = http_call(f"{proxy.base}/sendMessage", data=body,
                               headers={"Content-Type": "application/json"})

    assert (status, json.loads(answer)) == (200, {"ok": True, "result": {"message_id": 7}})
    seen = proxy.fake.requests[0]
    assert seen.path == f"/bot{TOKEN}/sendMessage"
    assert seen.verb == "POST"
    assert seen.body == body


def test_an_error_reaches_the_caller_verbatim(proxy, http_call) -> None:
    """Limits are diagnosed, not absorbed: retry_after must survive the hop."""
    flood = {"ok": False, "error_code": 429, "description": "Too Many Requests",
             "parameters": {"retry_after": 17}}
    proxy.fake.queue(429, flood)

    status, answer = http_call(f"{proxy.base}/sendMessage", data=b"{}",
                               headers={"Content-Type": "application/json"})

    assert status == 429
    assert json.loads(answer) == flood


def test_a_get_is_forwarded_as_a_get_with_its_query(proxy, http_call) -> None:
    proxy.fake.queue(200, {"ok": True, "result": {"username": "claude_channel_bot"}})

    status, answer = http_call(f"{proxy.base}/getChat?chat_id=-100")

    assert status == 200
    assert json.loads(answer)["result"]["username"] == "claude_channel_bot"
    assert proxy.fake.requests[0].verb == "GET"
    assert proxy.fake.requests[0].path == f"/bot{TOKEN}/getChat?chat_id=-100"


@pytest.mark.parametrize("method", ["getUpdates", "getupdates", "setWebhook",
                                    "deleteWebhook", "close", "logOut"])
def test_a_denied_method_never_reaches_telegram(proxy, http_call, method) -> None:
    status, answer = http_call(f"{proxy.base}/{method}", data=b"{}",
                               headers={"Content-Type": "application/json"})

    assert status == 403
    envelope = json.loads(answer)
    assert envelope["ok"] is False
    assert "telegram-hitl proxy" in envelope["description"]
    assert proxy.fake.requests == []
    assert _records(proxy.log_path)[0]["kind"] == "denied"


def test_every_denied_method_states_why(proxy) -> None:
    assert set(DENIED) == {"getupdates", "setwebhook", "deletewebhook", "close", "logout"}
    assert all(reason for reason in DENIED.values())


def test_a_call_is_logged_with_its_response_and_its_caller(proxy, http_call) -> None:
    proxy.fake.queue(200, {"ok": True, "result": {"message_id": 7}})

    http_call(f"{proxy.base}/sendMessage",
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


def test_a_non_json_body_is_logged_as_text(proxy, http_call) -> None:
    http_call(f"{proxy.base}/sendMessage", data=b"chat_id=-100&text=why",
              headers={"Content-Type": "application/x-www-form-urlencoded"})

    assert _records(proxy.log_path)[0]["params"] == "chat_id=-100&text=why"


def test_an_unreachable_telegram_is_reported_and_logged(tmp_path, http_call) -> None:
    """The channel being down must look different from a human being slow."""
    log_path = tmp_path / "channel.jsonl"
    log = ChannelLog(log_path)
    server = ProxyServer(("127.0.0.1", 0), log,
                         api_base="http://127.0.0.1:1", token=TOKEN)
    threading.Thread(target=server.serve_forever, daemon=True).start()

    status, answer = http_call(f"http://127.0.0.1:{server.server_port}/sendMessage",
                               data=b"{}", headers={"Content-Type": "application/json"})

    server.shutdown()
    server.server_close()
    log.close()
    assert status == 502
    assert "telegram-hitl proxy" in json.loads(answer)["description"]
    fault = _records(log_path)[0]
    assert (fault["kind"], fault["source"], fault["state"]) == ("fault", "forward", "failing")


def test_concurrent_senders_all_succeed_and_are_all_logged(proxy, http_call) -> None:
    """Outbound needs no coordination — the measurement the design rests on."""
    results: list[int] = []
    lock = threading.Lock()

    def send(n: int) -> None:
        status, _ = http_call(f"{proxy.base}/sendMessage",
                              data=json.dumps({"text": f"q{n}"}).encode(),
                              headers={"Content-Type": "application/json"})
        with lock:
            results.append(status)

    threads = [threading.Thread(target=send, args=(n,)) for n in range(10)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert results == [200] * 10
    records = _records(proxy.log_path)
    assert len(records) == 10
    assert {r["params"]["text"] for r in records} == {f"q{n}" for n in range(10)}
