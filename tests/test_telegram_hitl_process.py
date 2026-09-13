"""Tests for the real process: the lock, the lifecycle records, and restart."""

import json
import os
import signal
import socket
import subprocess
import sys
import time
from pathlib import Path

import pytest

import claude_config


def _records(path: Path) -> list[dict]:
    if not path.exists():
        return []
    found = []
    with open(path, "rb") as handle:
        for raw in handle:
            if not raw.endswith(b"\n"):
                break
            found.append(json.loads(raw))
    return found


def _of_kind(path: Path, kind: str) -> list[dict]:
    return [r for r in _records(path) if r["kind"] == kind]


def _polls(fake) -> list[dict]:
    return [r.payload for r in fake.requests if r.method == "getUpdates"]


def _serving(state_dir: Path, timeout: float = 15.0) -> Path:
    """Wait until the process answers on the socket beside its lock."""
    deadline = time.monotonic() + timeout
    socket_path = state_dir / "proxy.sock"
    while time.monotonic() < deadline:
        if socket_path.exists():
            probe = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            probe.settimeout(2)
            try:
                probe.connect(str(socket_path))
                return socket_path
            except OSError:
                pass
            finally:
                probe.close()
        time.sleep(0.05)
    raise AssertionError("the proxy did not start serving in time")


@pytest.fixture
def launch(tmp_path, fake_telegram):
    """Start the real process the way a session would, against the fake Bot API."""
    started: list[subprocess.Popen] = []
    source_root = Path(claude_config.__file__).resolve().parents[1]
    fake_telegram.default_delay = 0.2

    def start(*, state_dir: Path | None = None, token: str | None = "42:test-token",
              stateless: bool = False):
        environment = os.environ | {
            "TELEGRAM_HITL_STATE_DIR": str(state_dir or tmp_path / "state"),
            "TELEGRAM_HITL_API_BASE": fake_telegram.base,
            "PYTHONPATH": str(source_root),
        }
        if stateless:
            environment.pop("TELEGRAM_HITL_STATE_DIR")
        if token is None:
            environment.pop("TELEGRAM_BOT_TOKEN", None)
            environment["TELEGRAM_HITL_TOKEN_FILE"] = str(tmp_path / "token.env")
        else:
            environment["TELEGRAM_BOT_TOKEN"] = token
        process = subprocess.Popen([sys.executable, "-m", "claude_config.telegram_hitl"],
                                   env=environment, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE, text=True)
        started.append(process)
        return process

    yield start

    for process in started:
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()


def test_the_socket_sits_beside_the_lock_and_is_no_looser_than_the_log(
        launch, tmp_path) -> None:
    """One directory carries the lock, the log and the address, so a participant
    that can see the channel's state can reach the process holding it — there is
    no second fact to look up and no way for the two to disagree.

    Its mode matches the log's: reaching the socket and reading the log take the
    same identity, so a participant can do both or neither rather than half the
    job with no clue which half is missing.
    """
    launch()
    socket_path = _serving(tmp_path / "state")

    assert socket_path == tmp_path / "state" / "proxy.sock"
    assert socket_path.parent == (tmp_path / "state" / "proxy.lock").parent
    assert socket_path.stat().st_mode & 0o777 == (
        tmp_path / "state" / "channel.jsonl").stat().st_mode & 0o777


def test_an_unset_state_dir_stops_the_process_loudly(launch) -> None:
    """With no shared directory named, a proxy that started would take a lock
    nobody else holds and a stream everybody else is already reading."""
    process = launch(stateless=True)

    assert process.wait(timeout=15) != 0
    assert "TELEGRAM_HITL_STATE_DIR" in process.stderr.read()


def test_a_stale_socket_file_does_not_block_a_start(launch, tmp_path) -> None:
    """A killed proxy cannot unlink its own socket, so the file outlives it and
    bind would fail on an address nothing is serving. Holding the lock is what
    proves the file is stale, which is why the unlink happens only after it."""
    state = tmp_path / "state"
    first = launch()
    socket_path = _serving(state)

    first.kill()
    first.wait(timeout=10)
    assert socket_path.exists(), "the test needs a socket the dead process left behind"

    launch()
    assert _serving(state) == socket_path


def test_a_second_proxy_refuses_to_start_and_leaves_the_first_serving(
        launch, tmp_path, unix_call) -> None:
    """Telegram does not protect a running consumer, so exclusion is local."""
    first = launch()
    socket_path = _serving(tmp_path / "state")

    second = launch()
    assert second.wait(timeout=15) != 0
    assert "another proxy holds" in second.stderr.read()

    assert first.poll() is None
    status, answer = unix_call(socket_path, "getMe")
    assert (status, json.loads(answer)["ok"]) == (200, True)


def test_startup_and_shutdown_leave_a_record(launch, tmp_path) -> None:
    """A watcher must be able to tell a down channel from a slow human."""
    process = launch()
    socket_path = _serving(tmp_path / "state")

    process.send_signal(signal.SIGTERM)
    assert process.wait(timeout=15) == 0

    lifecycle = _of_kind(tmp_path / "state" / "channel.jsonl", "proxy")
    assert lifecycle[0]["event"] == "started"
    assert lifecycle[0]["pid"] == process.pid
    assert lifecycle[0]["socket"] == str(socket_path)
    assert lifecycle[-1]["event"] == "stopped"
    assert "SIGTERM" in lifecycle[-1]["reason"]


def test_a_signal_during_startup_still_leaves_a_stopped_record(launch, tmp_path) -> None:
    """The `started` record must never stand as the log's last word.

    A watcher reads a trailing `started` as a channel that is up, so a process
    that dies to the default signal disposition after writing one is
    indistinguishable from a human who has not replied. The handlers therefore
    have to be in place before the record exists, not merely before the drain.
    """
    state = tmp_path / "state"
    process = launch()

    socket_path = state / "proxy.sock"
    deadline = time.monotonic() + 15
    while not socket_path.exists() and time.monotonic() < deadline:
        pass
    assert socket_path.exists(), "the proxy never bound its socket"
    process.send_signal(signal.SIGTERM)

    assert process.wait(timeout=15) == 0
    lifecycle = _of_kind(state / "channel.jsonl", "proxy")
    assert lifecycle[-1]["event"] == "stopped"
    assert "SIGTERM" in lifecycle[-1]["reason"]


def test_a_restart_resumes_from_the_persisted_offset(launch, tmp_path, fake_telegram) -> None:
    batches = [json.dumps({"ok": True, "result": [
        {"update_id": 41, "message": {"text": "answer"}}]}).encode()]

    def answer(recorded) -> tuple[int, bytes]:
        """Keyed on the method: the readiness getMe must not eat the batch."""
        if recorded.method != "getUpdates":
            return 200, b'{"ok":true,"result":{}}'
        if batches:
            return 200, batches.pop(0)
        time.sleep(0.2)
        return 200, b'{"ok":true,"result":[]}'

    fake_telegram.handler = answer
    first = launch()
    _serving(tmp_path / "state")
    log_path = tmp_path / "state" / "channel.jsonl"

    deadline = time.monotonic() + 15
    while not _of_kind(log_path, "inbound") and time.monotonic() < deadline:
        time.sleep(0.05)
    assert _of_kind(log_path, "inbound")[0]["update"]["update_id"] == 41

    # The record is fsynced before the offset advances, so waiting on the record
    # is not waiting on the offset: a signal landing between them leaves nothing
    # persisted, and the restart correctly re-fetches from 0 instead of resuming.
    offset_file = tmp_path / "state" / "offset"
    deadline = time.monotonic() + 15
    while not offset_file.exists() and time.monotonic() < deadline:
        time.sleep(0.05)
    assert offset_file.read_text().strip() == "42"

    first.send_signal(signal.SIGTERM)
    assert first.wait(timeout=15) == 0
    fake_telegram.requests.clear()

    launch()
    _serving(tmp_path / "state")
    deadline = time.monotonic() + 15
    while not _polls(fake_telegram) and time.monotonic() < deadline:
        time.sleep(0.05)
    assert _polls(fake_telegram)[0]["offset"] == 42


def test_a_start_that_fails_is_recorded_too(launch, tmp_path) -> None:
    """A failed start must not leave the previous run's `started` as the log's
    last word, because a watcher reads that as a channel that is up.

    A state directory too deep for sun_path is the realistic shape: the path is
    far below PATH_MAX, so the log opens without complaint and the failure lands
    after the log is already the thing recording it.
    """
    state = tmp_path / ("deep" * 20) / "state"
    process = launch(state_dir=state)

    assert process.wait(timeout=20) != 0
    assert "sun_path" in process.stderr.read()

    lifecycle = _of_kind(state / "channel.jsonl", "proxy")
    assert [r["event"] for r in lifecycle] == ["stopped"]
    assert "sun_path" in lifecycle[0]["reason"]


def test_a_stale_lock_file_does_not_block_a_start(launch, tmp_path) -> None:
    """The lock lives on the descriptor, not in the file, so a process that died
    without cleaning up leaves nothing to clear. The pid written there is for a
    human reading it and must not be mistaken for the lock itself."""
    state = tmp_path / "state"
    state.mkdir(parents=True)
    (state / "proxy.lock").write_text("999999\n")

    launch()

    _serving(state)
    assert int((state / "proxy.lock").read_text()) != 999999


def test_a_crashing_drain_records_why_it_stopped(launch, tmp_path, fake_telegram) -> None:
    """A watcher has to be able to tell a dead channel from a slow human, so the
    reason a drain died belongs in the log and not only in an unread stderr.

    An update with no update_id is appended and fsynced, and then kills the drain
    on the one field it does interpret — the fatal path, since continuing past an
    update it cannot account for would lose a human's answer.
    """
    def answer(recorded) -> tuple[int, bytes]:
        if recorded.method != "getUpdates":
            return 200, b'{"ok":true,"result":{}}'
        return 200, b'{"ok":true,"result":[{"no_update_id":1}]}'

    fake_telegram.handler = answer

    process = launch()

    assert process.wait(timeout=20) != 0
    lifecycle = _of_kind(tmp_path / "state" / "channel.jsonl", "proxy")
    assert lifecycle[0]["event"] == "started"
    assert lifecycle[-1]["event"] == "stopped"
    assert "KeyError" in lifecycle[-1]["reason"]


@pytest.mark.parametrize("content, named", [
    (None, "token.env"),                  # no token file at all
    ("OTHER=1\n", "TELEGRAM_BOT_TOKEN"),  # a token file with no usable token
])
def test_a_misconfigured_token_stops_the_process_loudly(launch, tmp_path, content,
                                                        named) -> None:
    """Either way it exits non-zero with a backtrace naming its own cause, rather
    than starting and presenting as a channel nobody happens to be answering on.

    The two faults raise different exceptions — an absent file is a
    FileNotFoundError from the read, a file without the key is the RuntimeError
    config.token() raises — and each names the thing the operator has to fix."""
    if content is not None:
        (tmp_path / "token.env").write_text(content)

    process = launch(token=None)

    assert process.wait(timeout=15) != 0
    assert named in process.stderr.read()
