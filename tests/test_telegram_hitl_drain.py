"""Tests for the drain: the single update consumer and its durability ordering."""

import contextlib
import json
import threading
import time
from pathlib import Path

import pytest

from claude_config.telegram_hitl import drain
from claude_config.telegram_hitl.log import ChannelLog, ErrorTransitions

TOKEN = "42:test-token"


def _records(path: Path) -> list[dict]:
    """Complete records only: the drain may be mid-append while a test reads."""
    if not path.exists():
        return []
    found = []
    with open(path, "rb") as handle:
        for raw in handle:
            if not raw.endswith(b"\n"):
                break
            found.append(json.loads(raw))
    return found


def _inbound_ids(path: Path) -> list[int]:
    return [r["update"]["update_id"] for r in _records(path) if r["kind"] == "inbound"]


def _faults(path: Path) -> list[dict]:
    return [r for r in _records(path) if r["kind"] == "fault"]


def _batch(*updates: dict) -> tuple[int, bytes]:
    return 200, json.dumps({"ok": True, "result": list(updates)}).encode()


def _pace(fake, answers: list[tuple[int, bytes]]) -> None:
    """Answer each queued response in order, then long-poll-ish empties.

    The real server holds a poll open for 25 seconds. The fake must not answer
    an empty poll instantly or the drain spins the CPU for the whole test.
    """
    remaining = list(answers)

    def answer(_recorded) -> tuple[int, bytes]:
        if remaining:
            return remaining.pop(0)
        time.sleep(0.05)
        return 200, b'{"ok":true,"result":[]}'

    fake.handler = answer


def _wait_until(predicate, timeout: float = 5.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return
        time.sleep(0.01)
    raise AssertionError("condition was not met within the timeout")


@contextlib.contextmanager
def _running(log: ChannelLog, tmp_path: Path, fake):
    """The drain in a thread, with backoffs short enough for a test."""
    stop = threading.Event()
    thread = threading.Thread(
        target=drain.run,
        args=(log, ErrorTransitions(log, "drain")),
        kwargs=dict(api_base=fake.base, token=TOKEN, offset_path=tmp_path / "offset",
                    stop=stop, backoff_first=0.01, backoff_cap=0.02),
        daemon=True)
    thread.start()
    try:
        yield
    finally:
        stop.set()
        thread.join(timeout=5)
        assert not thread.is_alive()


def test_updates_are_appended_and_the_offset_advances(tmp_path, fake_telegram) -> None:
    log = ChannelLog(tmp_path / "channel.jsonl")
    _pace(fake_telegram, [_batch({"update_id": 41, "message": {"text": "one"}},
                                 {"update_id": 42, "message": {"text": "two"}})])

    with _running(log, tmp_path, fake_telegram):
        _wait_until(lambda: len(fake_telegram.requests) >= 2)
    log.close()

    assert _inbound_ids(tmp_path / "channel.jsonl") == [41, 42]
    assert (tmp_path / "offset").read_text().strip() == "43"
    assert fake_telegram.requests[0].payload["offset"] == 0
    assert fake_telegram.requests[1].payload["offset"] == 43


def test_the_log_is_written_before_telegram_is_told_to_forget(tmp_path, fake_telegram) -> None:
    """Advancing the offset is what makes an update unrecoverable, so the record
    must already be on disk. The fake answers as a function of the request, so it
    can read the log at the exact moment a poll carries the advanced offset."""
    log_path = tmp_path / "channel.jsonl"
    log = ChannelLog(log_path)
    seen: list[tuple[int, list[int]]] = []

    def answer(recorded) -> tuple[int, bytes]:
        offset = recorded.payload["offset"]
        seen.append((offset, _inbound_ids(log_path)))
        if offset == 0:
            return _batch({"update_id": 11, "message": {"text": "one"}},
                          {"update_id": 12, "message": {"text": "two"}})
        time.sleep(0.05)
        return 200, b'{"ok":true,"result":[]}'

    fake_telegram.handler = answer

    with _running(log, tmp_path, fake_telegram):
        _wait_until(lambda: len(seen) >= 2)
    log.close()

    assert seen[0] == (0, [])
    assert seen[1] == (13, [11, 12])


def test_repeated_poll_failures_log_one_transition_and_then_a_clearance(
        tmp_path, fake_telegram) -> None:
    log = ChannelLog(tmp_path / "channel.jsonl")
    failure = (500, b'{"ok":false,"error_code":500,"description":"Internal Server Error"}')
    _pace(fake_telegram, [failure, failure, failure,
                          _batch({"update_id": 5, "message": {"text": "late"}})])

    with _running(log, tmp_path, fake_telegram):
        _wait_until(lambda: _inbound_ids(tmp_path / "channel.jsonl") == [5])
        _wait_until(lambda: len(_faults(tmp_path / "channel.jsonl")) == 2)
    log.close()

    entered, cleared = _faults(tmp_path / "channel.jsonl")
    assert entered["state"] == "failing"
    assert entered["signature"] == "getUpdates:http500"
    assert "Internal Server Error" in entered["detail"]
    assert (cleared["state"], cleared["occurrences"]) == ("cleared", 3)


def test_a_stolen_stream_is_logged_and_polling_continues(tmp_path, fake_telegram) -> None:
    """409 means another poller seized the stream. The drain says so and keeps
    trying, because the interloper is usually short-lived and exiting would hand
    the channel over for good."""
    log = ChannelLog(tmp_path / "channel.jsonl")
    _pace(fake_telegram, [
        (409, b'{"ok":false,"error_code":409,"description":"Conflict: terminated by '
              b'other getUpdates request"}'),
        _batch({"update_id": 9, "message": {"text": "recovered"}})])

    with _running(log, tmp_path, fake_telegram):
        _wait_until(lambda: _inbound_ids(tmp_path / "channel.jsonl") == [9])
        _wait_until(lambda: len(_faults(tmp_path / "channel.jsonl")) == 2)
    log.close()

    entered, cleared = _faults(tmp_path / "channel.jsonl")
    assert entered["signature"] == "getUpdates:http409"
    assert "terminated by other getUpdates request" in entered["detail"]
    assert cleared["state"] == "cleared"


def test_an_unparseable_answer_is_a_fault_not_a_crash(tmp_path, fake_telegram) -> None:
    log = ChannelLog(tmp_path / "channel.jsonl")
    _pace(fake_telegram, [(200, b"<html>504 Gateway Time-out</html>"),
                          _batch({"update_id": 3, "message": {"text": "fine"}})])

    with _running(log, tmp_path, fake_telegram):
        _wait_until(lambda: _inbound_ids(tmp_path / "channel.jsonl") == [3])
    log.close()

    assert _faults(tmp_path / "channel.jsonl")[0]["signature"] == "getUpdates:unparseable"


def test_an_unreachable_telegram_is_retried(tmp_path, fake_telegram) -> None:
    log = ChannelLog(tmp_path / "channel.jsonl")
    stop = threading.Event()
    thread = threading.Thread(
        target=drain.run,
        args=(log, ErrorTransitions(log, "drain")),
        kwargs=dict(api_base="http://127.0.0.1:1", token=TOKEN,
                    offset_path=tmp_path / "offset", stop=stop,
                    backoff_first=0.01, backoff_cap=0.02),
        daemon=True)
    thread.start()
    _wait_until(lambda: len(_faults(tmp_path / "channel.jsonl")) == 1)
    assert thread.is_alive(), "the drain died on a fault instead of retrying it"
    stop.set()
    thread.join(timeout=5)
    log.close()

    fault = _faults(tmp_path / "channel.jsonl")[0]
    assert fault["signature"].startswith("getUpdates:URLError")
    assert fault["state"] == "failing"
    assert thread.is_alive() is False


def test_a_failure_to_record_is_fatal(tmp_path, fake_telegram) -> None:
    """Continuing past an unrecorded update would silently drop a human's answer."""
    log = ChannelLog(tmp_path / "channel.jsonl")
    log.close()
    _pace(fake_telegram, [_batch({"update_id": 1, "message": {"text": "lost"}})])

    with pytest.raises(OSError):
        drain.run(log, ErrorTransitions(log, "drain"), api_base=fake_telegram.base,
                  token=TOKEN, offset_path=tmp_path / "offset",
                  stop=threading.Event(), backoff_first=0.01, backoff_cap=0.02)


def test_a_persisted_offset_is_resumed(tmp_path, fake_telegram) -> None:
    log = ChannelLog(tmp_path / "channel.jsonl")
    (tmp_path / "offset").write_text("77\n")
    _pace(fake_telegram, [])

    with _running(log, tmp_path, fake_telegram):
        _wait_until(lambda: len(fake_telegram.requests) >= 1)
    log.close()

    assert fake_telegram.requests[0].payload["offset"] == 77
