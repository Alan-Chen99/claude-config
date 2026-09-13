"""Tests for the proxy's state: where it lives, and how records are written."""

import json
import os
import threading
from datetime import datetime
from pathlib import Path
from unittest import mock

import pytest

from claude_config.telegram_hitl import config
from claude_config.telegram_hitl.log import ChannelLog, ErrorTransitions


def _records(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines()]


def test_state_paths_follow_the_state_dir_override(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("TELEGRAM_HITL_STATE_DIR", str(tmp_path / "chan"))
    assert config.state_dir() == tmp_path / "chan"
    assert config.log_path() == tmp_path / "chan" / "channel.jsonl"
    assert config.offset_path() == tmp_path / "chan" / "offset"
    assert config.lock_path() == tmp_path / "chan" / "proxy.lock"
    assert config.port_path() == tmp_path / "chan" / "port"


def test_token_is_read_from_the_channel_env_file(monkeypatch, tmp_path) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text('# a comment\nTELEGRAM_BOT_TOKEN="123:secret"\n')
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.setenv("TELEGRAM_HITL_TOKEN_FILE", str(env_file))
    assert config.token() == "123:secret"


def test_the_environment_wins_over_the_token_file(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "from-env")
    monkeypatch.setenv("TELEGRAM_HITL_TOKEN_FILE", str(tmp_path / "absent"))
    assert config.token() == "from-env"


def test_a_missing_token_raises_rather_than_defaulting(monkeypatch, tmp_path) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text("SOMETHING_ELSE=1\n")
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.setenv("TELEGRAM_HITL_TOKEN_FILE", str(env_file))
    with pytest.raises(RuntimeError, match="TELEGRAM_BOT_TOKEN"):
        config.token()


def test_an_empty_token_value_is_treated_as_missing(monkeypatch, tmp_path) -> None:
    """A blanked token must fail here rather than as a 401 from Telegram later."""
    env_file = tmp_path / ".env"
    env_file.write_text('TELEGRAM_BOT_TOKEN=\nOTHER=1\n')
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.setenv("TELEGRAM_HITL_TOKEN_FILE", str(env_file))
    with pytest.raises(RuntimeError, match="TELEGRAM_BOT_TOKEN"):
        config.token()


def test_an_export_prefix_is_accepted(monkeypatch, tmp_path) -> None:
    """A shell-sourceable file must not report the token it contains as absent."""
    env_file = tmp_path / ".env"
    env_file.write_text("export TELEGRAM_BOT_TOKEN=123:secret\n")
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.setenv("TELEGRAM_HITL_TOKEN_FILE", str(env_file))
    assert config.token() == "123:secret"


def test_the_last_assignment_wins(monkeypatch, tmp_path) -> None:
    """What a shell and dotenv both do, so a rotated token appended below wins."""
    env_file = tmp_path / ".env"
    env_file.write_text("TELEGRAM_BOT_TOKEN=old\nTELEGRAM_BOT_TOKEN=new\n")
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.setenv("TELEGRAM_HITL_TOKEN_FILE", str(env_file))
    assert config.token() == "new"


def test_append_writes_one_timestamped_json_line_per_record(tmp_path) -> None:
    log = ChannelLog(tmp_path / "channel.jsonl")
    log.append({"kind": "inbound", "update": {"update_id": 1}})
    log.append({"kind": "proxy", "event": "started"})
    log.close()

    records = _records(tmp_path / "channel.jsonl")
    assert [r["kind"] for r in records] == ["inbound", "proxy"]
    assert records[0]["update"] == {"update_id": 1}
    assert datetime.fromisoformat(records[0]["ts"]) <= datetime.fromisoformat(records[1]["ts"])


def test_the_log_directory_is_created_on_demand(tmp_path) -> None:
    log = ChannelLog(tmp_path / "deep" / "nested" / "channel.jsonl")
    log.append({"kind": "proxy", "event": "started"})
    log.close()
    assert (tmp_path / "deep" / "nested" / "channel.jsonl").exists()


def test_concurrent_writers_never_interleave_a_line(tmp_path) -> None:
    """O_APPEND plus exactly one write syscall per record is the whole mechanism."""
    path = tmp_path / "channel.jsonl"

    def writer(number: int) -> None:
        log = ChannelLog(path)
        for sequence in range(50):
            log.append({"kind": "outbound", "writer": number, "seq": sequence,
                        "pad": "x" * 500})
        log.close()

    threads = [threading.Thread(target=writer, args=(n,)) for n in range(8)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    records = _records(path)
    assert {(r["writer"], r["seq"]) for r in records} == {
        (n, s) for n in range(8) for s in range(50)
    }


def test_a_short_write_raises_and_bounds_the_damage_to_one_line(tmp_path) -> None:
    """Unterminated bytes swallow the next record, which breaks every reader of
    the file permanently. A short write must raise, and leave one bad line."""
    path = tmp_path / "channel.jsonl"
    log = ChannelLog(path)
    real_write = os.write
    calls: list[bytes] = []

    def short_once(fd: int, data: bytes) -> int:
        calls.append(data)
        return real_write(fd, data[:-5] if len(calls) == 1 else data)

    with mock.patch("os.write", short_once):
        with pytest.raises(OSError, match="short write"):
            log.append({"kind": "inbound", "update": {"update_id": 1}})
    log.append({"kind": "inbound", "update": {"update_id": 2}})
    log.close()

    lines = path.read_bytes().splitlines(keepends=True)
    assert len(lines) == 2
    assert all(line.endswith(b"\n") for line in lines)
    with pytest.raises(json.JSONDecodeError):
        json.loads(lines[0])
    assert json.loads(lines[1])["update"]["update_id"] == 2


def test_repeated_faults_log_one_transition_then_one_clearance(tmp_path) -> None:
    log = ChannelLog(tmp_path / "channel.jsonl")
    faults = ErrorTransitions(log, "drain")
    for _ in range(3):
        faults.failed("getUpdates:http409", "terminated by other getUpdates request")
    faults.ok()
    faults.ok()
    log.close()

    records = _records(tmp_path / "channel.jsonl")
    assert [(r["state"], r.get("occurrences")) for r in records] == [
        ("failing", None), ("cleared", 3)]
    assert records[0]["signature"] == "getUpdates:http409"
    assert records[0]["source"] == "drain"


def test_a_changed_signature_closes_the_previous_state(tmp_path) -> None:
    log = ChannelLog(tmp_path / "channel.jsonl")
    faults = ErrorTransitions(log, "drain")
    faults.failed("a", "first")
    faults.failed("a", "first")
    faults.failed("b", "second")
    log.close()

    records = _records(tmp_path / "channel.jsonl")
    assert [(r["state"], r["signature"], r.get("occurrences")) for r in records] == [
        ("failing", "a", None), ("cleared", "a", 2), ("failing", "b", None)]


def test_a_healthy_source_writes_nothing(tmp_path) -> None:
    log = ChannelLog(tmp_path / "channel.jsonl")
    ErrorTransitions(log, "drain").ok()
    log.close()
    assert (tmp_path / "channel.jsonl").read_text() == ""


def test_concurrent_reporters_log_one_transition_per_episode(tmp_path) -> None:
    """The forwarder shares one tracker across every request thread, so the
    check, the mutation and the append have to be one step.

    The alternation matters: a repeated signature alone takes the increment
    path, which never blocks and so never yields mid-update. It is `_clear`'s
    fsync, inside the critical section, that opens the window this exercises.
    """
    log = ChannelLog(tmp_path / "channel.jsonl")
    faults = ErrorTransitions(log, "forward")
    barrier = threading.Barrier(12)

    def hammer() -> None:
        barrier.wait()
        for _ in range(40):
            faults.failed("forward:URLError", "unreachable")
            faults.ok()

    threads = [threading.Thread(target=hammer) for _ in range(12)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    faults.ok()
    log.close()

    records = _records(tmp_path / "channel.jsonl")
    states = [r["state"] for r in records]
    assert all(a != b for a, b in zip(states, states[1:])), f"state repeated: {states[:8]}"
    assert sum(r.get("occurrences", 0) for r in records) == 480
