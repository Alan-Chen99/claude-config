"""One question, one answer, one acknowledgement, through the real process.

Every other test drives a single layer. This one proves the layers fit, and that
the reader in `skills/telegram-hitl/listen.py` works against what the proxy
actually writes — which nothing else checks.
"""

import json
import os
import runpy
import signal
import subprocess
import sys
import time
from pathlib import Path

import pytest

import claude_config

SCRIPT = Path(__file__).resolve().parents[1] / "skills" / "telegram-hitl" / "listen.py"


def _answering_fake(fake) -> None:
    """A Bot API that answers by method, and delivers a reply once asked."""
    asked: list[int] = []
    delivered: list[bool] = []

    def answer(recorded) -> tuple[int, bytes]:
        if recorded.method == "sendMessage":
            asked.append(42)
            return 200, json.dumps({"ok": True, "result": {"message_id": 42}}).encode()
        if recorded.method == "createForumTopic":
            return 200, json.dumps({"ok": True, "result": {
                "message_thread_id": 6, "name": recorded.payload["name"]}}).encode()
        if recorded.method == "setMessageReaction":
            return 200, b'{"ok":true,"result":true}'
        if recorded.method == "getUpdates":
            if asked and not delivered:
                delivered.append(True)
                return 200, json.dumps({"ok": True, "result": [{
                    "update_id": 77, "message": {
                        # Higher than the question's id: a chat's message ids
                        # come from one counter, so an answer always outnumbers
                        # what it answers, and a reader uses that to tell a new
                        # message from one it has already dealt with.
                        "message_id": 99, "message_thread_id": 6,
                        "is_topic_message": True, "text": "yes, ship it",
                        "reply_to_message": {"message_id": asked[0],
                                             "text": "Ship it?"}}}]}).encode()
            time.sleep(0.2)
            return 200, b'{"ok":true,"result":[]}'
        return 200, b'{"ok":true,"result":{}}'

    fake.handler = answer


@pytest.fixture
def proxy_process(tmp_path, fake_telegram):
    """The real process, against the fake, torn down however the test ends."""
    _answering_fake(fake_telegram)
    state = tmp_path / "state"
    process = subprocess.Popen(
        [sys.executable, "-m", "claude_config.telegram_hitl"],
        env=os.environ | {
            "TELEGRAM_HITL_STATE_DIR": str(state),
            "TELEGRAM_HITL_API_BASE": fake_telegram.base,
            "TELEGRAM_BOT_TOKEN": "42:end-to-end",
            "PYTHONPATH": str(Path(claude_config.__file__).resolve().parents[1]),
        },
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    try:
        deadline = time.monotonic() + 20
        while not (state / "proxy.sock").exists() and time.monotonic() < deadline:
            time.sleep(0.05)
        assert (state / "proxy.sock").exists(), "the proxy never bound its socket"
        yield process, state, state / "proxy.sock"
    finally:
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()


def test_a_whole_cycle_runs_through_the_real_process(proxy_process, unix_call) -> None:
    process, state, socket_path = proxy_process
    log = state / "channel.jsonl"
    script = runpy.run_path(str(SCRIPT))
    records, inbox, inbound_state, topics = (
        script[name] for name in ("records", "inbox", "inbound_state", "topics"))

    def call(method: str, payload: dict) -> dict:
        status, answer = unix_call(
            socket_path, method, data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json", "X-Session-Id": "end-to-end"})
        assert status == 200, answer
        return json.loads(answer)

    assert inbound_state(records(log)) == "up"

    topic = call("createForumTopic", {"chat_id": -100, "name": "research: alpha"})
    thread = topic["result"]["message_thread_id"]
    asked = call("sendMessage", {"chat_id": -100, "message_thread_id": thread,
                                 "text": "Ship it?"})

    deadline = time.monotonic() + 20
    found = None
    while found is None and time.monotonic() < deadline:
        found = next(inbox(records(log), thread, asked["result"]["message_id"]), None)
        time.sleep(0.05)
    assert found is not None, "the skill's recipe never found the human's reply"
    assert found["text"] == "yes, ship it"
    assert found["is_topic_message"] is True

    assert call("setMessageReaction", {
        "chat_id": -100, "message_id": found["message_id"],
        "reaction": [{"type": "emoji", "emoji": "\N{THUMBS UP SIGN}"}]})["ok"] is True

    # The Bot API has no getForumTopics, so this is the only registry there is.
    assert topics(records(log)) == {thread: "research: alpha"}
    assert inbound_state(records(log)) == "up"

    process.send_signal(signal.SIGTERM)
    assert process.wait(timeout=20) == 0

    # The design's central promise: a down channel does not read as a slow human.
    assert inbound_state(records(log)) == "down: SIGTERM"
    assert [r["kind"] for r in records(log)] == [
        "proxy", "outbound", "outbound", "inbound", "outbound", "proxy"]
    assert {r["session"] for r in records(log)
            if r["kind"] == "outbound"} == {"end-to-end"}
