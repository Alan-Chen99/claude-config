# Telegram HITL Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the local Bot API proxy and the agent-facing skill described in `docs/superpowers/specs/2026-09-12-telegram-hitl-design.md`, so any number of concurrent Claude Code sessions can ask a human a question and read the answer.

**Architecture:** One long-lived process holds an exclusive `flock`, the bot token, and the single `getUpdates` cursor. It forwards any Bot API call from any session to Telegram unchanged and returns Telegram's own status and body verbatim, appending both directions plus its own faults to one JSONL log. The log is the only read interface. A skill carries the working rules and the API traps, because the proxy deliberately knows nothing.

**Tech Stack:** Python 3.14 standard library only — `urllib.request`, `http.server`, `fcntl`, `os.write`/`os.fsync`. No new dependencies. Tests are pytest integration tests against a fake Bot API served in-process.

---

## Decisions this plan locks in

The spec deliberately excludes implementation detail. These are the choices it leaves open, with what forced each one.

| Decision | Cause |
| --- | --- |
| Transport is HTTP on `127.0.0.1`, not a Unix socket | An agent must be able to call it with `curl` or stdlib `urllib` and no special flag; a Unix socket needs `--unix-socket` or a custom transport, which is knowledge the skill would have to carry. The token file is `0600` in a single-user container, so loopback exposure is not a privilege change. |
| URL shape is `http://127.0.0.1:<port>/<method>` | Telegram's own URL minus `/bot<token>`, so the substitution is mechanical for anyone who knows the Bot API. |
| Port defaults to `18420`, overridable by `TELEGRAM_HITL_PORT`; the bound port is written to `<state>/port` | The number is the first value chosen and nothing depends on it. The file exists so tests can bind port 0 and so a human never has to guess. |
| State lives in `~/.claude/channels/telegram-hitl/` | A sibling of the first-party plugin's `telegram/` directory, never inside it: that plugin is one of the components this one must not run concurrently with. |
| Denylist matches lowercased method names | Bot API method names are case-insensitive in the URL, so a denylist keyed on exact spelling is bypassed by `getupdates`. |
| The HTTP verb is preserved, not inferred | Pass-through: an agent's GET stays a GET. |
| `X-Session-Id` request header is copied into the log record, uninterpreted | The spec requires the log to be "a faithful record of who did what"; without a caller tag it records what but not who. |
| Backoff is one ladder for every poll fault: 1s doubling to a 60s cap | Simplicity. A 409 gets the same ladder as a network error — see the hazard below. |
| A 409 is logged as a fault and polling continues | The interloper is usually another session's short-lived poller, so automatic recovery matters for an unattended overnight wait, and exiting would hand the channel over permanently. **Hazard:** because a newcomer wins the stream, our retry can steal it back, and two pollers can flap — splitting a human's messages between two logs. The fault records make the contention visible; the fix is the spec's "exactly one drain" prerequisite, not a retry policy. This is the one question the spec left open that this plan answers by judgement. |
| No `[project.scripts]` entry point | `python -m claude_config.telegram_hitl` works in any checkout without reinstalling console scripts. |
| `deleteWebhook` is denied for `drop_pending_updates`, not for webhook exclusivity | The spec's parenthetical compresses both webhook methods into one reason. The accurate one: `setWebhook` disables `getUpdates`, while `deleteWebhook` can discard updates Telegram is still holding — the only irrecoverable loss in the system. Same denylist, truer reasons. |
| `ErrorTransitions` holds a lock across its state check, mutation and append | The forwarder shares one instance across every request thread of a threaded HTTP server. Measured unlocked: 12 threads reporting one fault signature produced 948 records with 728 duplicate adjacent states, and 545 counted occurrences for 480 calls — the fault channel corrupting exactly the signal the design relies on. |
| A short write terminates the damaged bytes with a newline before raising | The partial bytes cannot be taken back, and unterminated they swallow the next record: measured, a reader then dies with `JSONDecodeError` on the pair and everything appended afterwards is unreachable for good. A newline bounds the damage to one line. |
| A method name's *shape* is validated separately from the denylist | The denylist names the dangerous methods; it cannot also answer for every spelling that resolves to them. Measured without a shape check: `/getUpdates/`, `/get%55pdates`, `/%67etUpdates` and `/sendMessage/../getUpdates` all passed it and were forwarded with the denied name intact. The check constrains characters, not which methods pass, so the denylist decision stands. |
| A chunked request body is refused with 411 rather than forwarded | It carries no `Content-Length`, so it reads as empty. Measured: the body was dropped and the caller got a success — a send the agent believes it made. Refusing is the only answer that does not interpret a body. |
| A `getUpdates` result that is not a list is retried, not fatal | Measured: an object there reached the append loop and died on a `TypeError`, taking the channel down until a human restarted it. A malformed payload is a transient upstream fault like an unparseable one, and the design reserves fatality for failing to record an update. |
| `upstream.call` raises `URLError` for every unreachable or unusable answer | Both callers watch for `URLError`, and `urlopen` wraps only what fails while *sending*. Measured escaping: `ConnectionResetError`, `TimeoutError`, `BadStatusLine`. An uncaught one kills the drain in its own thread, which reaches a waiting session as a human who has not replied — the failure this design exists to prevent. |
| A forwarder handler that raises is logged, not fatal | Its answer is lost either way and stderr is read by nobody, so the fault has to reach the log to exist. Unlike the drain's equivalent it is not fatal: a dropped send is the caller's to retry and it sees the broken connection, while a dropped update is gone for good. |
| No code anywhere branches on chat layout | The spec's three layouts use the same primitives, so the layout is a chat id in a file and nothing else. A branch would be the first thing to rot when the DM layout is finally verified. |

**Not built, deliberately.** The spec excludes exactly-once claiming of answers,
a separate question ledger, token pooling, and static per-session assignment. An
implementer who adds deduplication or a session roster has broken the design, not
completed it: a session re-reading the same answer is wanted idempotency, and the
population of sessions is unbounded and unnamed. The DM layout remains unverified
and nothing depends on it.

## Log record shapes

Every record is one JSON object on one line, with an ISO-8601 UTC `ts` first. Agents read these; nothing else is an interface.

```json
{"ts":"...","kind":"proxy","event":"started","pid":123,"port":18420}
{"ts":"...","kind":"proxy","event":"stopped","reason":"_Stopped('SIGTERM')"}
{"ts":"...","kind":"inbound","update":{"update_id":11,"message":{}}}
{"ts":"...","kind":"outbound","session":"abc","method":"sendMessage","query":"","params":{},"elapsed_ms":84,"status":200,"response":{}}
{"ts":"...","kind":"denied","session":"abc","method":"getUpdates","reason":"..."}
{"ts":"...","kind":"fault","source":"drain","state":"failing","signature":"getUpdates:http409","detail":"..."}
{"ts":"...","kind":"fault","source":"drain","state":"cleared","signature":"getUpdates:http409","occurrences":7}
```

`ts` on an `outbound` record is completion time; `elapsed_ms` recovers the start.

One shape the proxy never writes: a reader that meets a line damaged by a failed
write yields `{"kind": "damaged", "raw": "..."}` in its place, so the damage stays
visible and the records after it stay readable.

## File structure

**Create:**

| Path | Responsibility |
| --- | --- |
| `src/claude_config/telegram_hitl/__init__.py` | empty package marker |
| `src/claude_config/telegram_hitl/config.py` | where state lives, what to talk to, how to read the token — every value env-overridable so tests need no network |
| `src/claude_config/telegram_hitl/log.py` | the append-only JSONL log and the error-transition tracker |
| `src/claude_config/telegram_hitl/upstream.py` | one Bot API call, returning Telegram's answer including its errors |
| `src/claude_config/telegram_hitl/server.py` | the forwarder: denylist, pass-through, logging |
| `src/claude_config/telegram_hitl/drain.py` | the single `getUpdates` consumer and the durability ordering |
| `src/claude_config/telegram_hitl/__main__.py` | the process: lock, lifecycle records, signals, wiring |
| `tests/conftest.py` | the fake Bot API fixture and an HTTP client helper |
| `tests/test_telegram_hitl_state.py` | config and log |
| `tests/test_telegram_hitl_forwarding.py` | the forwarder, in-process |
| `tests/test_telegram_hitl_drain.py` | the drain, in-process |
| `tests/test_telegram_hitl_process.py` | the real process as a subprocess: lock, lifecycle, restart |
| `tests/test_telegram_hitl_skill.py` | the skill's code recipes actually run |
| `tests/test_telegram_hitl_end_to_end.py` | one whole cycle through the real process, driven by the skill's recipes |
| `skills/telegram-hitl/SKILL.md` | the agent-facing rules, recipes and API traps |

**Modify:** `CLAUDE.md` (the `src/claude_config/` table), `skills/CLAUDE.md` (the Subdirectories table).

---

### Task 1: Where state lives, and how it is written

**Files:**
- Create: `src/claude_config/telegram_hitl/__init__.py`
- Create: `src/claude_config/telegram_hitl/config.py`
- Create: `src/claude_config/telegram_hitl/log.py`
- Test: `tests/test_telegram_hitl_state.py`

- [x] **Step 1: Write the failing tests**

Create `tests/test_telegram_hitl_state.py`:

```python
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
```

- [x] **Step 2: Run the tests to verify they fail**

Run: `cd /root/claude-config-work2 && uv run pytest tests/test_telegram_hitl_state.py -q`
Expected: collection error — `ModuleNotFoundError: No module named 'claude_config.telegram_hitl'`

- [x] **Step 3: Write the package and `config.py`**

Create `src/claude_config/telegram_hitl/__init__.py` as an empty file.

Create `src/claude_config/telegram_hitl/config.py`:

```python
"""Where the proxy's state lives and what it talks to.

Every value is environment-overridable so tests can point the proxy at a fake
Bot API and a scratch directory instead of the live channel.

State sits beside the first-party telegram plugin's directory rather than in
it: that plugin runs its own poller, and per the design's "exactly one drain"
prerequisite the two must never share anything.
"""

import os
from pathlib import Path

DEFAULT_STATE_DIR = Path.home() / ".claude" / "channels" / "telegram-hitl"
DEFAULT_TOKEN_FILE = Path.home() / ".claude" / "channels" / "telegram" / ".env"
DEFAULT_API_BASE = "https://api.telegram.org"
DEFAULT_PORT = 18420


def state_dir() -> Path:
    return Path(os.environ.get("TELEGRAM_HITL_STATE_DIR", DEFAULT_STATE_DIR))


def log_path() -> Path:
    return state_dir() / "channel.jsonl"


def offset_path() -> Path:
    return state_dir() / "offset"


def lock_path() -> Path:
    return state_dir() / "proxy.lock"


def port_path() -> Path:
    """The port actually bound, so a caller never has to guess it."""
    return state_dir() / "port"


def api_base() -> str:
    return os.environ.get("TELEGRAM_HITL_API_BASE", DEFAULT_API_BASE)


def port() -> int:
    """0 asks the kernel for a free port; the bound one lands in port_path()."""
    return int(os.environ.get("TELEGRAM_HITL_PORT", DEFAULT_PORT))


def token() -> str:
    """The bot token, from the environment or the channel's .env file.

    Parsed directly rather than through dotenv, which would load the repo's own
    .env and export into os.environ — neither of which this process wants.

    An `export` prefix is accepted and the last assignment wins, matching what a
    shell would do with the same file, so a rotated token appended to the end is
    the one used. An empty value counts as absent: a blanked token has to fail
    here rather than as an opaque 401 from Telegram.
    """
    from_environment = os.environ.get("TELEGRAM_BOT_TOKEN")
    if from_environment:
        return from_environment
    path = Path(os.environ.get("TELEGRAM_HITL_TOKEN_FILE", DEFAULT_TOKEN_FILE))
    found = ""
    for line in path.read_text().splitlines():
        key, separator, value = line.strip().removeprefix("export ").partition("=")
        if separator and key.strip() == "TELEGRAM_BOT_TOKEN" and value.strip():
            found = value.strip().strip("\"'")
    if found:
        return found
    raise RuntimeError(f"TELEGRAM_BOT_TOKEN is not in the environment or in {path}")
```

- [x] **Step 4: Run the tests to verify the failure has moved**

The test module imports `log` at the top, so nothing in it can run until Step 5.
This step confirms `config` is no longer what is missing.

Run: `cd /root/claude-config-work2 && uv run pytest tests/test_telegram_hitl_state.py -q 2>&1 | tail -3`
Expected: collection error naming `claude_config.telegram_hitl.log`, not `config`

- [x] **Step 5: Write `log.py`**

Create `src/claude_config/telegram_hitl/log.py`:

```python
"""The append-only JSONL channel log: the system's only read interface.

Many processes append here at once, so every record is one O_APPEND write
syscall — on a local filesystem the kernel then orders whole records and no two
can interleave. Each write is fsynced because the drain's durability ordering
depends on a record being on disk before Telegram is told to forget the update.
"""

import json
import os
import threading
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


class ChannelLog:
    """One open append handle. Cheap enough to hold per process."""

    def __init__(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        self._fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)

    def append(self, record: dict[str, Any]) -> None:
        """Write one record and fsync it. Raises on any failure to record."""
        line = json.dumps({"ts": datetime.now(UTC).isoformat(), **record},
                          ensure_ascii=False).encode() + b"\n"
        written = os.write(self._fd, line)
        if written != len(line):
            # The partial bytes are in the file already and cannot be taken back.
            # Terminating them bounds the damage to one unparseable line: without
            # a newline they swallow the next record, and every reader of the file
            # then fails on the pair and never reaches anything appended after it.
            os.write(self._fd, b"\n")
            os.fsync(self._fd)
            raise OSError(f"short write to channel log: {written} of {len(line)} bytes")
        os.fsync(self._fd)

    def close(self) -> None:
        os.close(self._fd)


class ErrorTransitions:
    """Log entering and leaving a failing state, not every occurrence.

    A stolen update stream fails every poll, and recording each one at poll rate
    would bury the log in identical lines. The interesting events are the edges.

    The lock is required rather than defensive: the forwarder shares one instance
    across every request thread, and the state check, the mutation and the append
    have to be one step or concurrent callers duplicate each other's transitions.
    """

    def __init__(self, log: ChannelLog, source: str) -> None:
        self._log = log
        self._source = source
        self._lock = threading.Lock()
        self._signature: str | None = None
        self._count = 0

    def failed(self, signature: str, detail: str) -> None:
        with self._lock:
            if signature == self._signature:
                self._count += 1
                return
            self._clear()
            self._signature = signature
            self._count = 1
            self._log.append({"kind": "fault", "source": self._source,
                              "state": "failing", "signature": signature,
                              "detail": detail})

    def ok(self) -> None:
        """No-op while healthy, so a working component writes nothing."""
        with self._lock:
            self._clear()

    def _clear(self) -> None:
        """Close any open failing episode. The caller holds the lock."""
        if self._signature is None:
            return
        self._log.append({"kind": "fault", "source": self._source, "state": "cleared",
                          "signature": self._signature, "occurrences": self._count})
        self._signature = None
        self._count = 0
```

- [x] **Step 6: Run the whole file to verify it passes**

Run: `cd /root/claude-config-work2 && uv run pytest tests/test_telegram_hitl_state.py -q`
Expected: 15 passed

- [x] **Step 7: Commit**

```bash
cd /root/claude-config-work2
git add src/claude_config/telegram_hitl/__init__.py \
        src/claude_config/telegram_hitl/config.py \
        src/claude_config/telegram_hitl/log.py \
        tests/test_telegram_hitl_state.py
git commit -m "$(cat <<'MSG'
feat(telegram-hitl): channel log and state paths

Records are one O_APPEND write each, fsynced, so concurrent senders cannot
interleave a line and the drain can order durability against the cursor.
Faults log transitions rather than occurrences.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>
MSG
)"
```

### Task 2: The forwarder

**Files:**
- Create: `src/claude_config/telegram_hitl/upstream.py`
- Create: `src/claude_config/telegram_hitl/server.py`
- Create: `tests/conftest.py`
- Test: `tests/test_telegram_hitl_forwarding.py`

- [x] **Step 1: Write the fake Bot API fixture**

Create `tests/conftest.py`:

```python
"""Shared fixtures: a stand-in Bot API, and an HTTP client that never raises."""

import json
import sys
import threading
import time
import urllib.error
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

import pytest


@dataclass
class Recorded:
    """One request the fake Bot API received."""

    path: str
    verb: str
    headers: dict[str, str]
    body: bytes

    @property
    def method(self) -> str:
        """The Bot API method name, with the token segment and query stripped."""
        return self.path.split("/", 2)[2].split("?")[0]

    @property
    def payload(self) -> Any:
        return json.loads(self.body) if self.body else None


@dataclass
class FakeTelegram:
    """Records every request and answers from a queue, or from a function.

    `handler` overrides the queue, which is how the durability-ordering test
    inspects the log at the exact moment a poll carries an advanced offset.
    """

    base: str = ""
    requests: list[Recorded] = field(default_factory=list)
    responses: list[tuple[int, bytes]] = field(default_factory=list)
    handler: Callable[[Recorded], tuple[int, bytes]] | None = None
    default: tuple[int, bytes] = (200, b'{"ok":true,"result":[]}')
    default_delay: float = 0.0
    _lock: threading.Lock = field(default_factory=threading.Lock)

    def queue(self, status: int, payload: Any) -> None:
        body = payload if isinstance(payload, bytes) else json.dumps(payload).encode()
        with self._lock:
            self.responses.append((status, body))

    def answer(self, recorded: Recorded) -> tuple[int, bytes]:
        with self._lock:
            self.requests.append(recorded)
            if self.handler is not None:
                return self.handler(recorded)
            if self.responses:
                return self.responses.pop(0)
        # Outside the lock, and delayed: the real server holds an empty poll open
        # for 25 seconds, and a fake that answers instantly makes the drain spin.
        time.sleep(self.default_delay)
        return self.default


def _handler_class(fake: FakeTelegram) -> type[BaseHTTPRequestHandler]:
    class Handler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def _reply(self) -> None:
            length = int(self.headers.get("Content-Length") or 0)
            status, body = fake.answer(Recorded(self.path, self.command,
                                                dict(self.headers), self.rfile.read(length)))
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        do_GET = _reply
        do_POST = _reply

        def log_message(self, *args: Any) -> None:
            """Silent: the test asserts on fake.requests, not on stderr."""

    return Handler


class _Server(ThreadingHTTPServer):
    daemon_threads = True

    def handle_error(self, request, client_address) -> None:
        """A proxy killed mid-poll drops its connection, which is a test ending
        rather than a fault of the fake. Its traceback in teardown reads exactly
        like a failure, so it is suppressed; everything else still prints."""
        if not isinstance(sys.exception(), (BrokenPipeError, ConnectionResetError)):
            super().handle_error(request, client_address)


@pytest.fixture
def fake_telegram():
    """A Bot API on loopback that the proxy can be pointed at."""
    fake = FakeTelegram()
    server = _Server(("127.0.0.1", 0), _handler_class(fake))
    fake.base = f"http://127.0.0.1:{server.server_port}"
    threading.Thread(target=server.serve_forever, daemon=True).start()
    yield fake
    server.shutdown()
    server.server_close()


@pytest.fixture
def http_call():
    """Call a URL and return (status, body); a 4xx/5xx is an answer, not a raise."""

    def call(url: str, *, data: bytes | None = None, headers: dict[str, str] | None = None,
             verb: str | None = None, timeout: float = 10.0) -> tuple[int, bytes]:
        request = urllib.request.Request(url, data=data, headers=headers or {},
                                         method=verb or ("POST" if data else "GET"))
        try:
            with urllib.request.urlopen(request, timeout=timeout) as answer:
                return answer.status, answer.read()
        except urllib.error.HTTPError as error:
            return error.code, error.read()

    return call
```

- [x] **Step 2: Write the failing forwarder tests**

Create `tests/test_telegram_hitl_forwarding.py`:

```python
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


def _faults(path: Path) -> list[dict]:
    return [r for r in _records(path) if r["kind"] == "fault"]


@pytest.fixture
def proxy(tmp_path, fake_telegram):
    """The forwarder in-process, pointed at the fake Bot API."""
    log_path = tmp_path / "channel.jsonl"
    log = ChannelLog(log_path)
    server = ProxyServer(("127.0.0.1", 0), log, api_base=fake_telegram.base, token=TOKEN)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    yield SimpleNamespace(base=f"http://127.0.0.1:{server.server_port}",
                          port=server.server_port, log_path=log_path, fake=fake_telegram)
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


@pytest.mark.parametrize("spelling", ["getUpdates/", "get%55pdates", "%67etUpdates",
                                     "sendMessage/../getUpdates"])
def test_a_denied_method_cannot_be_reached_by_respelling_it(proxy, http_call,
                                                            spelling) -> None:
    """Measured before the shape check existed: every one of these passed the
    denylist and reached Telegram with the denied name intact. Stealing the
    update cursor is the worst thing a caller can do to this system."""
    status, answer = http_call(f"{proxy.base}/{spelling}", data=b"{}",
                               headers={"Content-Type": "application/json"})

    assert status == 400
    assert "not a Bot API method name" in json.loads(answer)["description"]
    assert proxy.fake.requests == []


def test_a_chunked_body_is_refused_rather_than_forwarded_empty(proxy) -> None:
    """A chunked body carries no Content-Length, so it reads as empty. Forwarding
    it would be a send with no fields that the agent believes it made."""
    payload = b'{"chat_id":-100,"text":"a chunked message"}'
    sock = socket.create_connection(("127.0.0.1", proxy.port), timeout=10)
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
    sock = socket.create_connection(("127.0.0.1", proxy.port), timeout=10)
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


def test_an_upstream_that_never_answers_is_reported_and_logged(tmp_path, http_call,
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
    server = ProxyServer(("127.0.0.1", 0), log, token=TOKEN,
                         api_base=f"http://127.0.0.1:{listener.getsockname()[1]}")
    threading.Thread(target=server.serve_forever, daemon=True).start()

    status, answer = http_call(f"http://127.0.0.1:{server.server_port}/sendMessage",
                               data=b"{}", headers={"Content-Type": "application/json"})

    server.shutdown()
    server.server_close()
    log.close()
    listener.close()
    assert status == 502
    assert "telegram-hitl proxy" in json.loads(answer)["description"]
    assert _faults(log_path)[0]["source"] == "forward"


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
```

- [x] **Step 3: Run the tests to verify they fail**

Run: `cd /root/claude-config-work2 && uv run pytest tests/test_telegram_hitl_forwarding.py -q`
Expected: collection error — `ModuleNotFoundError: No module named 'claude_config.telegram_hitl.server'`

- [x] **Step 4: Write `upstream.py`**

Create `src/claude_config/telegram_hitl/upstream.py`:

```python
"""One Bot API call. Shared by the forwarder and the drain.

A 4xx or 5xx comes back as a Response rather than an exception: Telegram's
error bodies carry retry_after, REACTION_INVALID and the rest, which are the
useful part and must reach the caller verbatim.

Anything else is raised as a URLError, which is what both callers watch for.
urlopen only wraps what fails while sending the request; everything raised while
reading the answer comes through unwrapped, and each of these was measured
escaping: ConnectionResetError from a peer that closes, TimeoutError from one
that accepts and never answers, BadStatusLine from one that answers with
something that is not HTTP. A drain that misses any of them dies in its own
thread, which reaches a waiting session as a human who has not replied yet.
"""

import http.client
import urllib.error
import urllib.request
from dataclasses import dataclass


@dataclass(frozen=True)
class Response:
    status: int
    content_type: str
    body: bytes


def call(api_base: str, token: str, method: str, *, verb: str = "POST", query: str = "",
         body: bytes = b"", content_type: str = "", timeout: float = 30.0) -> Response:
    """Issue one request and return Telegram's own answer.

    Raises urllib.error.URLError when Telegram could not be reached or did not
    answer usably, which is the one case a caller has to decide about.
    """
    url = f"{api_base}/bot{token}/{method}"
    if query:
        url = f"{url}?{query}"
    headers = {"Content-Type": content_type} if content_type else {}
    request = urllib.request.Request(url, data=body or None, headers=headers, method=verb)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as answer:
            return Response(answer.status, answer.headers.get("Content-Type", ""),
                            answer.read())
    except urllib.error.HTTPError as error:
        return Response(error.code, error.headers.get("Content-Type", ""), error.read())
    except urllib.error.URLError:
        raise
    except (OSError, http.client.HTTPException) as error:
        raise urllib.error.URLError(error) from error
```

- [x] **Step 5: Write `server.py`**

Create `src/claude_config/telegram_hitl/server.py`:

```python
"""Forwards Bot API calls from any number of sessions, and logs each one.

It interprets nothing: it refuses the handful of methods that would break the
drain's invariants, passes everything else through unchanged, and hands back
Telegram's own status and body byte for byte. An agent therefore composes an
ordinary Bot API request and reads an ordinary Bot API answer, errors included.
"""

import json
import re
import sys
import time
import urllib.error
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

from claude_config.telegram_hitl import upstream
from claude_config.telegram_hitl.log import ChannelLog, ErrorTransitions

# Keyed on the lowercased name: Bot API method names are case-insensitive in the
# URL, so a denylist spelled exactly would be bypassed by "getupdates".
DENIED: dict[str, str] = {
    "getupdates": "the drain owns the only update cursor, and a second consumer evicts it",
    "setwebhook": "a webhook disables getUpdates, silently stopping the drain",
    "deletewebhook": "drop_pending_updates would discard updates Telegram is still holding",
    "close": "would invalidate the bot session the drain is polling on",
    "logout": "would invalidate the bot token",
}

# A Bot API method name is alphanumeric, so anything else is not one. Measured,
# without this check: /getUpdates/, /get%55pdates, /%67etUpdates and
# /sendMessage/../getUpdates all passed the denylist and reached Telegram with
# the denied name intact. The denylist names the dangerous methods; it cannot
# also answer for every spelling that resolves to them, so the shape is checked
# separately. This constrains the characters a method name may contain and
# nothing about which methods pass, so the denylist decision stands.
METHOD_NAME = re.compile(r"[A-Za-z][A-Za-z0-9]*\Z")

FORWARD_TIMEOUT = 30.0
IDLE_TIMEOUT = 120.0


def _envelope(code: int, description: str) -> bytes:
    """A Telegram-shaped error, marked as the proxy's own so it cannot be mistaken."""
    return json.dumps({"ok": False, "error_code": code,
                       "description": f"telegram-hitl proxy: {description}"}).encode()


def _decoded(raw: bytes) -> Any:
    """Parse JSON for a log meant to be read with jq; keep anything else as text."""
    if not raw:
        return None
    try:
        return json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError):
        return raw.decode("utf-8", errors="replace")


class _Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    timeout = IDLE_TIMEOUT
    server: "ProxyServer"

    def do_GET(self) -> None:
        method, _, query = self.path.lstrip("/").partition("?")
        self._forward(method, query, b"", "")

    def do_POST(self) -> None:
        method, _, query = self.path.lstrip("/").partition("?")
        if "Transfer-Encoding" in self.headers:
            # A chunked body carries no Content-Length, so it reads as empty and
            # would be forwarded as a send with no fields — which Telegram
            # answers by naming the fields it is missing, for a message the agent
            # believes it sent. Refuse rather than forward a body that is not
            # there.
            self._refuse(411, method, "send a body with Content-Length; a chunked "
                                      "body cannot be forwarded")
            return
        length = int(self.headers.get("Content-Length") or 0)
        self._forward(method, query, self.rfile.read(length),
                      self.headers.get("Content-Type", ""))

    def _forward(self, method: str, query: str, body: bytes, content_type: str) -> None:
        session = self.headers.get("X-Session-Id")
        if not METHOD_NAME.match(method):
            self._refuse(400, method, "not a Bot API method name")
            return
        denial = DENIED.get(method.lower())
        if denial is not None:
            self._refuse(403, method, denial)
            return

        started = time.monotonic()
        try:
            answer = upstream.call(self.server.api_base, self.server.token, method,
                                   verb=self.command, query=query, body=body,
                                   content_type=content_type, timeout=FORWARD_TIMEOUT)
        except urllib.error.URLError as error:
            self.server.faults.failed(f"forward:{type(error).__name__}", repr(error))
            self._answer(502, _envelope(502, f"cannot reach Telegram: {error}"))
            return

        self.server.faults.ok()
        self.server.log.append({
            "kind": "outbound", "session": session, "method": method, "query": query,
            "params": _decoded(body),
            "elapsed_ms": round((time.monotonic() - started) * 1000),
            "status": answer.status, "response": _decoded(answer.body),
        })
        self._answer(answer.status, answer.body, answer.content_type)

    def _refuse(self, code: int, method: str, reason: str) -> None:
        """Log and answer without forwarding. Every refusal takes this path."""
        self.server.log.append({"kind": "denied", "session": self.headers.get("X-Session-Id"),
                                "method": method, "reason": reason})
        self._answer(code, _envelope(code, reason))

    def _answer(self, status: int, body: bytes, content_type: str = "") -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type or "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args: Any) -> None:
        """Silent: the channel log is the record, and nobody reads this stderr."""


class ProxyServer(ThreadingHTTPServer):
    """Threaded because sends are stateless and safely parallel."""

    daemon_threads = True

    def __init__(self, address: tuple[str, int], log: ChannelLog, *,
                 api_base: str, token: str) -> None:
        super().__init__(address, _Handler)
        self.log = log
        self.api_base = api_base
        self.token = token
        self.faults = ErrorTransitions(log, "forward")

    def handle_error(self, request: object, client_address: object) -> None:
        """Record a handler that raised, where everyone is already looking.

        Its answer to the caller is lost either way and this server's stderr is
        read by nobody. Not fatal, unlike the drain's equivalent: a dropped send
        is the caller's to retry and it sees the broken connection, while a
        dropped update is gone for good.
        """
        error = sys.exception()
        try:
            self.faults.failed(f"handler:{type(error).__name__}", repr(error))
        except OSError:
            super().handle_error(request, client_address)  # the log is what failed
```

- [x] **Step 6: Run the tests to verify they pass**

Run: `cd /root/claude-config-work2 && uv run pytest tests/test_telegram_hitl_forwarding.py -q`
Expected: 21 passed

- [x] **Step 7: Check the new conftest did not disturb the existing suite**

Run: `cd /root/claude-config-work2 && uv run pytest tests/ -q 2>&1 | tail -3`
Expected: `365 passed` — 329 in the suite before this work, plus 15 from Task 1
and 21 from Task 2

- [x] **Step 8: Commit**

```bash
cd /root/claude-config-work2
git add src/claude_config/telegram_hitl/upstream.py \
        src/claude_config/telegram_hitl/server.py \
        tests/conftest.py tests/test_telegram_hitl_forwarding.py
git commit -m "$(cat <<'MSG'
feat(telegram-hitl): pass-through forwarder with an invariant denylist

Five methods can break the drain or the token; everything else is forwarded
untouched and Telegram's own status and body come back verbatim, so an error
reaches the agent that provoked it instead of being absorbed here.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>
MSG
)"
```

### Task 3: The drain

**Files:**
- Create: `src/claude_config/telegram_hitl/drain.py`
- Test: `tests/test_telegram_hitl_drain.py`

- [x] **Step 1: Write the failing drain tests**

Create `tests/test_telegram_hitl_drain.py`:

```python
"""Tests for the drain: the single update consumer and its durability ordering."""

import contextlib
import json
import threading
import time
from pathlib import Path

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
    """Continuing past an unrecorded update would silently drop a human's answer.

    Bounded by a join rather than run inline: if the guarantee regresses the
    drain polls forever, and a test for a fatal path has to fail rather than
    hang. Nothing else in this suite would stop it — there is no global timeout.
    """
    log = ChannelLog(tmp_path / "channel.jsonl")
    log.close()
    _pace(fake_telegram, [_batch({"update_id": 1, "message": {"text": "lost"}})])
    raised: list[BaseException] = []

    def record() -> None:
        try:
            drain.run(log, ErrorTransitions(log, "drain"), api_base=fake_telegram.base,
                      token=TOKEN, offset_path=tmp_path / "offset",
                      stop=threading.Event(), backoff_first=0.01, backoff_cap=0.02)
        except BaseException as error:  # noqa: BLE001 - re-raised by the assertion
            raised.append(error)

    thread = threading.Thread(target=record, daemon=True)
    thread.start()
    thread.join(timeout=5)

    assert not thread.is_alive(), "the drain kept polling on an unwritable log"
    assert isinstance(raised[0], OSError)


def test_a_persisted_offset_is_resumed(tmp_path, fake_telegram) -> None:
    log = ChannelLog(tmp_path / "channel.jsonl")
    (tmp_path / "offset").write_text("77\n")
    _pace(fake_telegram, [])

    with _running(log, tmp_path, fake_telegram):
        _wait_until(lambda: len(fake_telegram.requests) >= 1)
    log.close()

    assert fake_telegram.requests[0].payload["offset"] == 77
```

- [x] **Step 2: Run the tests to verify they fail**

Run: `cd /root/claude-config-work2 && uv run pytest tests/test_telegram_hitl_drain.py -q`
Expected: collection error — `ImportError: cannot import name 'drain'`

- [x] **Step 3: Write `drain.py`**

Create `src/claude_config/telegram_hitl/drain.py`:

```python
"""The single getUpdates consumer: poll, append, flush, advance. Nothing else.

Any other work here is work that can kill the one component nothing else can
replace — a newcomer cannot simply be started alongside it, because a second
consumer evicts the first. A dead drain reaches a waiting session as "the human
has not answered yet", which is the failure this whole design exists to prevent.

Its failure surface is therefore held to three cases: a failed poll, which it
retries; a failure to durably record an update, which is fatal because
continuing past it would silently drop a human's answer; and an update whose
update_id is missing or unusable, which is fatal for the same reason, since
there is then no safe offset to advance to.
"""

import json
import os
import threading
import urllib.error
from pathlib import Path

from claude_config.telegram_hitl import upstream
from claude_config.telegram_hitl.log import ChannelLog, ErrorTransitions

POLL_TIMEOUT = 25
BACKOFF_FIRST = 1.0
BACKOFF_CAP = 60.0


def read_offset(path: Path) -> int:
    """An absent offset means "whatever Telegram still holds" — the safe direction."""
    try:
        return int(path.read_text())
    except FileNotFoundError:
        return 0


def write_offset(path: Path, offset: int) -> None:
    """Replace atomically: a torn offset file would skip or repeat on restart."""
    temporary = path.with_suffix(".tmp")
    handle = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    try:
        os.write(handle, f"{offset}\n".encode())
        os.fsync(handle)
    finally:
        os.close(handle)
    os.replace(temporary, path)


def run(log: ChannelLog, faults: ErrorTransitions, *, api_base: str, token: str,
        offset_path: Path, stop: threading.Event, poll_timeout: int = POLL_TIMEOUT,
        backoff_first: float = BACKOFF_FIRST, backoff_cap: float = BACKOFF_CAP) -> None:
    """Drain updates until `stop` is set, or until a record cannot be written.

    The durability ordering is the whole mitigation for the system's only
    irrecoverable loss: every update is appended and fsynced before the next
    poll carries the advanced offset, which is what tells Telegram to forget it.

    `stop` is observed between polls and during a backoff, never mid-call: a poll
    already in flight runs to its own timeout first, so a caller wanting a prompt
    exit needs its own mechanism. The process raises from its signal handler,
    which is what makes SIGTERM prompt.
    """
    offset = read_offset(offset_path)
    backoff = backoff_first

    while not stop.is_set():
        try:
            answer = upstream.call(
                api_base, token, "getUpdates",
                body=json.dumps({"offset": offset, "timeout": poll_timeout}).encode(),
                content_type="application/json", timeout=poll_timeout + 10)
        except urllib.error.URLError as error:
            faults.failed(f"getUpdates:{type(error).__name__}", repr(error))
            backoff = _pause(stop, backoff, backoff_cap)
            continue

        if answer.status != 200:
            faults.failed(f"getUpdates:http{answer.status}",
                          answer.body.decode("utf-8", errors="replace")[:500])
            backoff = _pause(stop, backoff, backoff_cap)
            continue

        try:
            updates = json.loads(answer.body)["result"]
            if not isinstance(updates, list):
                # Raised into this handler: a result that is not a
                # list is the same kind of fault as one that will not parse, and
                # earns the same retry. Measured without this, an object here
                # reached the loop below and died on a TypeError, taking the
                # channel down until a human restarted it.
                raise TypeError(f"result is {type(updates).__name__}, not a list")
        except (json.JSONDecodeError, UnicodeDecodeError, KeyError, TypeError) as error:
            faults.failed("getUpdates:unparseable", repr(error))
            backoff = _pause(stop, backoff, backoff_cap)
            continue

        faults.ok()
        backoff = backoff_first
        for update in updates:
            log.append({"kind": "inbound", "update": update})
            # Fatal if update_id is missing or unusable, by the same logic as a
            # failure to record: there is no safe value to advance the offset to.
            # Skipping the update would either re-serve it forever or advance
            # past an answer that nothing accounted for.
            offset = update["update_id"] + 1
        if updates:
            write_offset(offset_path, offset)


def _pause(stop: threading.Event, backoff: float, cap: float) -> float:
    """Wait out the backoff, returning the next one. Interruptible by `stop`."""
    stop.wait(backoff)
    return min(backoff * 2, cap)
```

- [x] **Step 4: Run the tests to verify they pass**

Run: `cd /root/claude-config-work2 && uv run pytest tests/test_telegram_hitl_drain.py -q`
Expected: 8 passed

- [x] **Step 5: Commit**

```bash
cd /root/claude-config-work2
git add src/claude_config/telegram_hitl/drain.py tests/test_telegram_hitl_drain.py
git commit -m "$(cat <<'MSG'
feat(telegram-hitl): the single update drain

Every update is appended and fsynced before the next poll carries the advanced
offset, since advancing it is what makes an update unrecoverable. A failed poll
is retried and logged as a transition; a failure to record is fatal.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>
MSG
)"
```

### Task 4: The process

**Files:**
- Create: `src/claude_config/telegram_hitl/__main__.py`
- Test: `tests/test_telegram_hitl_process.py`

- [x] **Step 1: Write the failing process tests**

Create `tests/test_telegram_hitl_process.py`:

```python
"""Tests for the real process: the lock, the lifecycle records, and restart."""

import json
import os
import signal
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
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


def _serving(state_dir: Path, timeout: float = 15.0) -> int:
    """Wait until the process has bound a port and answers on it."""
    deadline = time.monotonic() + timeout
    port_file = state_dir / "port"
    while time.monotonic() < deadline:
        if port_file.exists():
            port = int(port_file.read_text())
            try:
                with urllib.request.urlopen(f"http://127.0.0.1:{port}/getMe",
                                            timeout=2) as answer:
                    answer.read()
                return port
            except urllib.error.HTTPError:
                return port
            except OSError:
                pass
        time.sleep(0.05)
    raise AssertionError("the proxy did not start serving in time")


@pytest.fixture
def launch(tmp_path, fake_telegram):
    """Start the real process the way a session would, against the fake Bot API."""
    started: list[subprocess.Popen] = []
    source_root = Path(claude_config.__file__).resolve().parents[1]
    fake_telegram.default_delay = 0.2

    def start(*, state_dir: Path | None = None, token: str | None = "42:test-token",
              port: int = 0):
        environment = os.environ | {
            "TELEGRAM_HITL_STATE_DIR": str(state_dir or tmp_path / "state"),
            "TELEGRAM_HITL_API_BASE": fake_telegram.base,
            "TELEGRAM_HITL_PORT": str(port),
            "PYTHONPATH": str(source_root),
        }
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


def test_the_bound_port_is_written_where_a_caller_can_read_it(launch, tmp_path) -> None:
    launch()
    port = _serving(tmp_path / "state")
    assert 1024 < port < 65536
    assert int((tmp_path / "state" / "port").read_text()) == port


def test_a_second_proxy_refuses_to_start_and_leaves_the_first_serving(
        launch, tmp_path) -> None:
    """Telegram does not protect a running consumer, so exclusion is local."""
    first = launch()
    port = _serving(tmp_path / "state")

    second = launch()
    assert second.wait(timeout=15) != 0
    assert "another proxy holds" in second.stderr.read()

    assert first.poll() is None
    with urllib.request.urlopen(f"http://127.0.0.1:{port}/getMe", timeout=5) as answer:
        assert json.loads(answer.read())["ok"] is True


def test_startup_and_shutdown_leave_a_record(launch, tmp_path) -> None:
    """A watcher must be able to tell a down channel from a slow human."""
    process = launch()
    port = _serving(tmp_path / "state")

    process.send_signal(signal.SIGTERM)
    assert process.wait(timeout=15) == 0

    lifecycle = _of_kind(tmp_path / "state" / "channel.jsonl", "proxy")
    assert lifecycle[0]["event"] == "started"
    assert lifecycle[0]["pid"] == process.pid
    assert lifecycle[0]["port"] == port
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
    last word, because a watcher reads that as a channel that is up."""
    held = socket.socket()
    held.bind(("127.0.0.1", 0))
    held.listen(1)
    try:
        process = launch(port=held.getsockname()[1])
        assert process.wait(timeout=20) != 0
        assert "Address already in use" in process.stderr.read()
    finally:
        held.close()

    lifecycle = _of_kind(tmp_path / "state" / "channel.jsonl", "proxy")
    assert [r["event"] for r in lifecycle] == ["stopped"]
    assert "in use" in lifecycle[0]["reason"]


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
```

- [x] **Step 2: Run the tests to verify they fail**

Run: `cd /root/claude-config-work2 && uv run pytest tests/test_telegram_hitl_process.py -q 2>&1 | tail -5`
Expected: failures — `No module named claude_config.telegram_hitl.__main__`

- [x] **Step 3: Write `__main__.py`**

Create `src/claude_config/telegram_hitl/__main__.py`:

```python
"""One process: take the lock, serve sends, drain updates.

The lock is load-bearing rather than defensive. A second getUpdates consumer is
not refused by Telegram — it evicts the first — so exclusion has to happen
locally, before any process reaches the network.

Run it as `python -m claude_config.telegram_hitl`.
"""

import errno
import fcntl
import os
import signal
import threading
from pathlib import Path

from claude_config.telegram_hitl import config, drain
from claude_config.telegram_hitl.log import ChannelLog, ErrorTransitions
from claude_config.telegram_hitl.server import ProxyServer

# The errnos flock reports when someone else holds the lock. Anything else — no
# locking on this filesystem, a bad descriptor — is a different fault, and
# calling it contention sends the operator hunting for a second proxy that does
# not exist.
CONTENDED = frozenset({errno.EACCES, errno.EAGAIN, errno.EWOULDBLOCK})


class _Stopped(Exception):
    """A signal asked for shutdown. Raised in the main thread to unblock the poll."""


def _acquire_lock(path: Path) -> int:
    """Hold an exclusive lock for the life of the process.

    The returned descriptor is deliberately never closed: closing it releases
    the lock, which would let a second drain start and evict this one.
    """
    handle = os.open(path, os.O_WRONLY | os.O_CREAT, 0o600)
    try:
        fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError as error:
        if error.errno not in CONTENDED:
            raise
        raise SystemExit(f"telegram-hitl: another proxy holds {path}; refusing to start")
    os.ftruncate(handle, 0)
    os.write(handle, f"{os.getpid()}\n".encode())
    return handle


def main() -> None:
    state = config.state_dir()
    state.mkdir(parents=True, exist_ok=True)
    token = config.token()
    _acquire_lock(config.lock_path())

    log = ChannelLog(config.log_path())

    # Everything after the log opens sits inside the try, so a start that fails
    # halfway is recorded as well. Measured without it: a port already in use
    # exited 1 and wrote nothing, leaving whatever the previous run wrote as the
    # log's last word — and a run killed outright leaves `started`, which a
    # watcher reads as a channel that is up.
    reason = "the drain returned"
    failed = False
    try:
        server = ProxyServer(("127.0.0.1", config.port()), log,
                             api_base=config.api_base(), token=token)
        config.port_path().write_text(f"{server.server_port}\n")
        log.append({"kind": "proxy", "event": "started", "pid": os.getpid(),
                    "port": server.server_port})
        print(f"telegram-hitl: 127.0.0.1:{server.server_port} -> {config.log_path()}",
              flush=True)
        threading.Thread(target=server.serve_forever, daemon=True).start()

        stop = threading.Event()

        def _signalled(number: int, _frame: object) -> None:
            stop.set()
            raise _Stopped(signal.Signals(number).name)

        signal.signal(signal.SIGTERM, _signalled)
        signal.signal(signal.SIGINT, _signalled)

        drain.run(log, ErrorTransitions(log, "drain"), api_base=config.api_base(),
                  token=token, offset_path=config.offset_path(), stop=stop)
    except _Stopped as signalled:
        reason = str(signalled)
    except BaseException as error:
        reason = repr(error)
        failed = True
        raise
    finally:
        try:
            log.append({"kind": "proxy", "event": "stopped", "reason": reason})
        except OSError:
            if not failed:
                raise  # nothing else is propagating, so this fault has to


if __name__ == "__main__":
    main()
```

- [x] **Step 4: Run the tests to verify they pass**

Run: `cd /root/claude-config-work2 && uv run pytest tests/test_telegram_hitl_process.py -q`
Expected: 9 passed

- [x] **Step 5: Run the whole suite**

Run: `cd /root/claude-config-work2 && uv run pytest tests/ -q 2>&1 | tail -3`
Expected: `382 passed` — 329 before this work, plus 15, 21, 8 and 9. Task 5 adds
the last 16, for 398.

- [x] **Step 6: Commit**

```bash
cd /root/claude-config-work2
git add src/claude_config/telegram_hitl/__main__.py tests/test_telegram_hitl_process.py
git commit -m "$(cat <<'MSG'
feat(telegram-hitl): the proxy process

An exclusive flock, taken before anything reaches the network, is what keeps a
second drain from evicting this one. Startup, shutdown and the bound port are
recorded so a waiting session can tell a down channel from a slow human.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>
MSG
)"
```

### Task 5: The skill

The proxy deliberately knows nothing, so everything needed to work the channel
correctly is knowledge rather than API surface — and it has to live where a
fresh session will read it. The recipes are marked with HTML comments so the
test can execute them: documented code that is never run is documented code
that drifts.

**Files:**
- Create: `skills/telegram-hitl/SKILL.md`
- Test: `tests/test_telegram_hitl_skill.py`

- [x] **Step 1: Write the failing recipe tests**

Create `tests/test_telegram_hitl_skill.py`:

```python
"""The skill's recipes are executable, so they get executed here."""

from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

SKILL = Path(__file__).resolve().parents[1] / "skills" / "telegram-hitl" / "SKILL.md"


def _recipe(name: str) -> dict:
    """Exec one marked python block from the skill and return its namespace."""
    text = SKILL.read_text()
    marker = f"<!-- recipe: {name} -->"
    assert marker in text, f"the skill has no recipe marked {name}"
    opening = text.index("```python", text.index(marker))
    body = text[opening + len("```python"):text.index("```", opening + 3)]
    namespace: dict = {}
    exec(compile(body, str(SKILL), "exec"), namespace)
    return namespace


def test_the_log_reader_skips_a_partial_final_line(tmp_path) -> None:
    """The documented Python trap: a record still being appended has no newline."""
    path = tmp_path / "channel.jsonl"
    path.write_bytes(b'{"kind":"proxy","event":"started"}\n'
                     b'{"kind":"inbound","update":{"update_id":1}}\n'
                     b'{"kind":"inbound","update":{"upda')

    records = _recipe("read-log")["records"]

    assert [r["kind"] for r in records(path)] == ["proxy", "inbound"]


def test_the_log_reader_surfaces_a_damaged_line_and_keeps_going(tmp_path) -> None:
    """A failed write must not make everything appended after it unreadable."""
    path = tmp_path / "channel.jsonl"
    path.write_bytes(b'{"kind":"proxy","event":"started"}\n'
                     b'{"kind":"outbound","method":"sendMes\n'
                     b'{"kind":"inbound","update":{"update_id":9}}\n')

    records = _recipe("read-log")["records"]

    found = list(records(path))
    assert [r["kind"] for r in found] == ["proxy", "damaged", "inbound"]
    assert "sendMes" in found[1]["raw"]


def test_the_answer_finder_matches_the_reply_to_a_question(tmp_path) -> None:
    answer_to = _recipe("answers")["answer_to"]
    log = [
        {"kind": "inbound", "update": {"message": {"message_id": 50, "text": "hello"}}},
        {"kind": "inbound", "update": {"message": {
            "message_id": 51, "text": "yes, ship it",
            "reply_to_message": {"message_id": 49, "text": "should I ship?"}}}},
    ]

    assert answer_to(log, 49)["text"] == "yes, ship it"
    assert answer_to(log, 12) is None


def test_the_topic_registry_is_reconstructed_from_the_log() -> None:
    """There is no getForumTopics, so the log is the only registry there is."""
    topics = _recipe("topics")["topics"]
    log = [
        {"kind": "outbound", "method": "createForumTopic", "params": {"name": "alpha"},
         "response": {"ok": True, "result": {"message_thread_id": 6, "name": "alpha"}}},
        {"kind": "outbound", "method": "createForumTopic", "params": {"name": "beta"},
         "response": {"ok": True, "result": {"message_thread_id": 7, "name": "beta"}}},
        {"kind": "outbound", "method": "editForumTopic",
         "params": {"message_thread_id": 7, "name": "beta (renamed)"},
         "response": {"ok": True, "result": True}},
        {"kind": "outbound", "method": "createForumTopic", "params": {"name": "refused"},
         "response": {"ok": False, "description": "not enough rights to create a topic"}},
        {"kind": "outbound", "method": "deleteForumTopic",
         "params": {"message_thread_id": 6}, "response": {"ok": True, "result": True}},
        {"kind": "inbound", "update": {"message": {"message_id": 1}}},
    ]

    assert topics(log) == {7: "beta (renamed)"}


def test_the_inbound_state_distinguishes_a_dead_channel_from_a_quiet_one() -> None:
    """The whole point of logging faults: silence has two causes. A single
    failed poll is not one of them — measured live, one cleared 26 seconds
    later, and treating it as a dead channel abandoned an answer still coming.
    """
    inbound_state = _recipe("health")["inbound_state"]
    now = datetime.now(UTC)

    def at(seconds_ago: float) -> str:
        return (now - timedelta(seconds=seconds_ago)).isoformat()

    started = [{"ts": at(600), "kind": "proxy", "event": "started"}]
    quiet = started + [{"ts": at(500), "kind": "inbound", "update": {}}]
    blip = quiet + [{"ts": at(5), "kind": "fault", "source": "drain",
                     "state": "failing", "signature": "getUpdates:URLError"}]
    stuck = quiet + [{"ts": at(900), "kind": "fault", "source": "drain",
                      "state": "failing", "signature": "getUpdates:http409"}]

    assert inbound_state([]) == "down: never started"
    assert inbound_state(quiet) == "up"
    assert inbound_state(blip) == "up"
    assert inbound_state(stuck) == "down: getUpdates:http409"
    assert inbound_state(blip + [{"ts": at(1), "kind": "fault", "source": "drain",
                                  "state": "cleared",
                                  "signature": "getUpdates:URLError"}]) == "up"
    # a stopped proxy is not a blip, however recently it stopped
    assert inbound_state(started + [{"ts": at(2), "kind": "proxy", "event": "stopped",
                                     "reason": "SIGTERM"}]) == "down: SIGTERM"
    # a failed send says nothing about whether answers are arriving
    assert inbound_state(quiet + [{"ts": at(900), "kind": "fault", "source": "forward",
                                   "state": "failing",
                                   "signature": "forward:URLError"}]) == "up"


def test_the_skill_names_the_session_variable_that_exists() -> None:
    """Claude Code sets CLAUDE_CODE_SESSION_ID and there is no CLAUDE_SESSION_ID.
    An example reading the wrong one sends an empty header rather than failing,
    so the log's record of who called comes out blank — worse than an error.
    """
    text = SKILL.read_text()
    assert "$CLAUDE_CODE_SESSION_ID" in text
    assert "$CLAUDE_SESSION_ID" not in text


@pytest.mark.parametrize("status", ["`400`", "`403`", "`411`", "`502`"])
def test_the_skill_documents_every_refusal_the_proxy_returns(status) -> None:
    """An agent that meets a refusal has only this document to explain it, and
    three of the four come from the proxy rather than from Telegram."""
    assert status in SKILL.read_text()


@pytest.mark.parametrize("trap", [
    "is_topic_message",          # message_thread_id carries two different ids
    "MESSAGE_ID_INVALID",        # reactability is type-specific
    "REACTION_INVALID",          # the reaction alphabet is fixed
    "General",                   # the General topic is not addressable
    "migrate_to_chat_id",        # enabling Topics changes the chat id
    "partial",                   # reading a file under append needs care
])
def test_the_skill_still_carries_every_trap_that_cost_time(trap) -> None:
    """These were measured the hard way; an edit must not quietly drop one."""
    assert trap in SKILL.read_text()
```

- [x] **Step 2: Run the tests to verify they fail**

Run: `cd /root/claude-config-work2 && uv run pytest tests/test_telegram_hitl_skill.py -q 2>&1 | tail -3`
Expected: 16 failed — `FileNotFoundError` on `skills/telegram-hitl/SKILL.md`

- [x] **Step 3: Write the skill**

Create `skills/telegram-hitl/SKILL.md`:

````markdown
---
name: telegram-hitl
description: Use when a session needs a human decision it cannot make alone - asking a question and waiting hours for an answer, or listening for an unsolicited correction mid-run. Covers the local Telegram proxy, its log, forum-topic choice, and the Bot API traps.
---

# Telegram human-in-the-loop

Reach the human by making ordinary Bot API calls against a local proxy, and read
their answers out of one append-only log. Any number of sessions do this at
once. Nothing is assigned to you, and no chat, topic or message is yours alone.

| | |
| --- | --- |
| Proxy | `http://127.0.0.1:18420` (the bound port is in `~/.claude/channels/telegram-hitl/port`) |
| Log | `~/.claude/channels/telegram-hitl/channel.jsonl` |
| Chat id | `~/.claude/channels/telegram-hitl/chat_id` |

If `chat_id` is absent, the channel is not set up on this machine, and reading it
anyway just puts an empty value in your request. Setting it up needs a human: a
Telegram supergroup with Topics enabled, the bot added as an administrator with
Manage Topics, and the chat id written to that file. The Bot API can do none of
it — it can neither create a chat nor raise its own rights. `getChat` reporting
`is_forum: true` confirms the first two.

If the port does not answer, the proxy is not running:

```bash
UV_PROJECT_ENVIRONMENT=$HOME/.claude/venvs/claude-config \
agent-tools run --background --desc "telegram-hitl proxy" \
  uv run --project /repos/claude-config python -m claude_config.telegram_hitl
```

The environment variable is this repo's convention; without it `uv` would build
a `.venv` inside the canonical checkout. It refuses to start if another instance holds the lock, which is intended — one
process owns the update stream, and a second consumer would evict the first.

## Sending

Take any Bot API URL, drop `https://api.telegram.org/bot<token>`, and point what
is left at the proxy. What comes back is Telegram's own JSON.

```bash
curl -s -X POST http://127.0.0.1:18420/sendMessage \
  -H 'Content-Type: application/json' \
  -H "X-Session-Id: $CLAUDE_CODE_SESSION_ID" \
  -d "{\"chat_id\": $(cat ~/.claude/channels/telegram-hitl/chat_id), \"message_thread_id\": 6, \"text\": \"Ship it?\"}"
```

`X-Session-Id` is optional and uninterpreted; it lands in the log so the record
says who called.

Refused with `403`: `getUpdates`, `setWebhook`, `deleteWebhook`, `close`,
`logOut`. Each would break the one update stream or the token. Everything else
passes through.

Three more refusals are the proxy's own rather than Telegram's, and each names
`telegram-hitl proxy` in its `description` so you can tell which is which:

| | |
| --- | --- |
| `400` | The method name is not alphanumeric. `sendMessage` is fine; `sendMessage/`, `send%4dessage` and `x/../getUpdates` are not — a respelling that resolves to a denied method would otherwise walk straight past the denylist. |
| `411` | The body was sent chunked, so it carries no `Content-Length` and would forward as empty. Send a body with a length. |
| `502` | Telegram could not be reached or did not answer usably. The same fault is in the log, so a watcher sees it too. |

**Errors arrive as themselves** and nothing is retried for you — `retry_after`,
`REACTION_INVALID`, `message thread not found`, `not enough rights to create a
topic`. Read the error and decide. If you are hitting flood control at
human-in-the-loop volumes, that is a defect in what you are doing, not a limit
to pace around.

## Reading

The log is the only read interface. Every line is one JSON object: `inbound` (a
Telegram update, verbatim), `outbound` (a call with its response), `denied`,
`fault` (the channel's own faults), `proxy` (start and stop).

<!-- recipe: read-log -->
```python
import json


def records(path):
    """Every complete record in the channel log, oldest first.

    A final line with no newline is a record another process is still
    appending. Python's file iterator hands it over anyway, so stop there.

    A line that will not parse is a record damaged by a failed write. It is
    yielded as one, so the damage stays visible and the records after it stay
    readable.
    """
    with open(path, "rb") as handle:
        for raw in handle:
            if not raw.endswith(b"\n"):
                return
            try:
                yield json.loads(raw)
            except json.JSONDecodeError:
                yield {"kind": "damaged", "raw": raw.decode("utf-8", errors="replace")}
```

## Asking, then waiting

Send the question, keep the `message_id` from the response, and watch for a
reply to it. An inbound reply carries the full text of the message it answers
under `reply_to_message`, so you need no question ledger.

<!-- recipe: answers -->
```python
def answer_to(records, message_id):
    """The human's first reply to the message with this id, or None."""
    for record in records:
        if record["kind"] != "inbound":
            continue
        message = record["update"].get("message") or {}
        if (message.get("reply_to_message") or {}).get("message_id") == message_id:
            return message
    return None
```

Waits here are measured in hours, so wait against the file, not against a socket.
Write a small waiter to your scratchpad and background it — it exits on the
answer, which produces exactly one notification:

```bash
agent-tools run --background --desc "await human" python3 <your-scratchpad>/waiter.py 51
```

It needs nothing but the standard library, so it runs under plain `python3`.

A waiter that only looks for an answer cannot tell *no answer yet* from *the
channel is down*. Check both — but do not abandon a wait on the first fault you
see. A failed poll is ordinary, and the recipe below already forgives a recent
one; only a fault that persists means the channel needs you.

<!-- recipe: health -->
```python
from datetime import UTC, datetime


def inbound_state(records, failing_for=180.0):
    """"up", or "down: <cause>" — whether a human's answer can still reach you.

    Silence has two causes wanting opposite responses: keep waiting, or go fix
    the channel. Only drain faults are decisive here; a failed send says nothing
    about whether answers are arriving.

    A drain fault younger than `failing_for` seconds still reads as up, because
    one failed poll is ordinary — Telegram resets a long poll and the next one
    succeeds. Measured live: two connection resets in a seven-minute run, each
    having happened once and cleared within 27 seconds, while a waiter that gave
    up the moment it saw one abandoned an answer that was still coming. Three
    minutes therefore forgives the routine case and still notices a genuinely
    dead channel quickly. A stopped proxy is never a blip, however recent.
    """
    state, since = "down: never started", None
    for record in records:
        if record["kind"] == "proxy":
            state = "up" if record["event"] == "started" else "down: " + record["reason"]
            since = None
        elif record["kind"] == "fault" and record["source"] == "drain":
            if record["state"] == "cleared":
                state, since = "up", None
            else:
                state, since = "down: " + record["signature"], record["ts"]
    if since is not None:
        age = (datetime.now(UTC) - datetime.fromisoformat(since)).total_seconds()
        if age < failing_for:
            return "up"
    return state
```

For **unsolicited** input instead — a correction or a stop arriving mid-run with
no question of yours to answer — use `Monitor` on the log. That is an open-ended
stream of occurrences, which is what a persistent monitor is for; a background
loop that exits on the first match is the wrong shape for it.

## Topics

The chat is a forum. Messages land in a topic, addressed by `message_thread_id`.

**Use an existing topic when your question is a natural continuation of it;
otherwise make a new one.** Nothing prescribes how many topics you may have, or
ties a topic to a session. Judge continuity, and remember the human has to read
the result.

There is no `getForumTopics` in the Bot API, so the log is the only registry:

<!-- recipe: topics -->
```python
def topics(records):
    """The forum's topics, by thread id. Every one is a logged createForumTopic."""
    found = {}
    for record in records:
        if record["kind"] != "outbound":
            continue
        response = record["response"]
        if not isinstance(response, dict) or not response.get("ok"):
            continue
        method = record["method"].lower()
        params = record["params"] or {}
        if method == "createforumtopic":
            found[response["result"]["message_thread_id"]] = response["result"]["name"]
        elif method == "editforumtopic" and "name" in params:
            found[params["message_thread_id"]] = params["name"]
        elif method == "deleteforumtopic":
            found.pop(params["message_thread_id"], None)
    return found
```

Create one with `createForumTopic` (`{"chat_id": ..., "name": "..."}`) and use
the `message_thread_id` it returns.

## Acknowledging

When you have read the human's answer, react to their message — from your own
script, once you actually have it. Nothing else reacts, so an unreacted message
is one nobody has taken, and that absence is informative.

```bash
CHAT=$(cat ~/.claude/channels/telegram-hitl/chat_id)
curl -s -X POST http://127.0.0.1:18420/setMessageReaction \
  -H 'Content-Type: application/json' \
  -d "{\"chat_id\": $CHAT, \"message_id\": 51, \"reaction\": [{\"type\":\"emoji\",\"emoji\":\"👍\"}]}"
```

## Traps

Each of these cost real time to find.

- **`message_thread_id` carries either a reply-chain id or a forum-topic id.**
  `is_topic_message` is the discriminator. Both ids come from the same per-chat
  counter, so a wrong value is never out of range — it just files an ordinary
  reply as a topic.
- **A forum's General topic cannot be addressed by thread id.** A conversation
  becomes routable only once a topic exists for it.
- **The reaction alphabet is fixed.** 👀 👍 🙏 🤔 🔥 ⚡ work; ✅ and 📝 return
  `REACTION_INVALID`. The obvious checkmark is specifically unavailable.
- **Reactability is type-specific and unpredictable.** `new_chat_members`
  accepts a reaction; chat-migration service messages return
  `MESSAGE_ID_INVALID`. Let a script crash on it — loud, local, harmless.
- **Enabling Topics migrates a group and changes its chat id.** The old id then
  returns `group chat was upgraded to a supergroup chat`, and
  `migrate_to_chat_id` is the forwarding pointer. Follow it rather than treating
  a stored chat id as stable.
- **Reading a file under append needs care in Python**, which yields a partial
  final line where a shell `read` loop does not. Use the reader above.
- **A human replying as an anonymous group admin arrives as
  `GroupAnonymousBot`**, not under their own name. The answer still correlates
  through `reply_to_message`, so nothing breaks — but `from` will not tell you
  who answered, and you should not claim it does.
- **Never start another poller.** The first-party `telegram` plugin and
  `telegram-bot-skill` each start their own, and a newcomer does not get
  refused — it seizes the stream and kills the existing consumer. A 409 in the
  log means exactly this has happened.
````

- [x] **Step 4: Run the tests to verify they pass**

Run: `cd /root/claude-config-work2 && uv run pytest tests/test_telegram_hitl_skill.py -q`
Expected: 16 passed

- [x] **Step 5: Commit**

```bash
cd /root/claude-config-work2
git add skills/telegram-hitl/SKILL.md tests/test_telegram_hitl_skill.py
git commit -m "$(cat <<'MSG'
feat(telegram-hitl): the agent-facing skill

The proxy interprets nothing, so working the channel correctly is knowledge
rather than API surface, and it has to live where a fresh session will read it.
Its recipes are executed by the tests, so documented code cannot drift.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>
MSG
)"
```

### Task 6: Documentation

**Files:**
- Modify: `CLAUDE.md` (the `src/claude_config/` module table)
- Modify: `skills/CLAUDE.md` (the Subdirectories table)

- [x] **Step 1: Add the module row**

In `CLAUDE.md`, in the `### src/claude_config/` table, after the
`claude_config.env_context` row, add:

```markdown
| `claude_config.telegram_hitl`   | Local Bot API proxy for human-in-the-loop over Telegram: one flock-guarded process owns the single `getUpdates` drain, forwards sends from any number of sessions, and appends both directions plus its own faults to one JSONL log. Design: `docs/superpowers/specs/2026-09-12-telegram-hitl-design.md` | `python -m claude_config.telegram_hitl` |
```

- [x] **Step 2: Add the skill row**

In `skills/CLAUDE.md`, in the Subdirectories table, after the `git-surgery/`
row, add:

```markdown
| `telegram-hitl/`      | Asking a human a question over Telegram and waiting hours for the answer: the local proxy, the channel log, topic choice, and the Bot API traps | When a session needs a human decision, or is reading or sending on the Telegram channel |
```

- [x] **Step 3: Verify no other reference needs updating**

Run: `cd /root/claude-config-work2 && grep -rn "telegram" --include="*.md" -il . | grep -v docs/superpowers | grep -v node_modules`
Expected: `CLAUDE.md`, `skills/CLAUDE.md`, `skills/telegram-hitl/SKILL.md` and nothing else

- [x] **Step 4: Commit**

```bash
cd /root/claude-config-work2
git add CLAUDE.md skills/CLAUDE.md
git commit -m "$(cat <<'MSG'
docs: register telegram-hitl in the module and skill tables

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>
MSG
)"
```

---

### Task 7: End to end

Every other task's tests drive one layer. None of them proves the layers fit, or
that the skill's recipes work against what the proxy actually writes — and the
recipes cannot be covered by anything else, because they live in a markdown
document and are only executed out of it.

This task adds one test that runs the real process against a fake Bot API and
drives a whole cycle with the skill's own code: create a topic, ask, wait for the
answer, acknowledge it, then stop and confirm the channel reads as down.

It carries its own launcher rather than reusing Task 4's, because it needs a fake
that answers by method — delivering the human's reply only once a question has
been asked — and because duplicating fifteen lines of setup is cheaper than
restructuring two tasks that are already reviewed.

**Files:**
- Test: `tests/test_telegram_hitl_end_to_end.py`

- [x] **Step 1: Write the test**

Create `tests/test_telegram_hitl_end_to_end.py`:

```python
"""One question, one answer, one acknowledgement, through the real process.

Every other test drives a single layer. This one proves the layers fit, and that
the recipes in `skills/telegram-hitl/SKILL.md` work against what the proxy
actually writes — which nothing else checks, since those recipes live in a
document and are only ever executed out of it.
"""

import json
import os
import signal
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

import pytest

import claude_config

SKILL = Path(__file__).resolve().parents[1] / "skills" / "telegram-hitl" / "SKILL.md"


def _recipe(name: str) -> dict:
    """Exec one marked python block from the skill and return its namespace."""
    text = SKILL.read_text()
    opening = text.index("```python", text.index(f"<!-- recipe: {name} -->"))
    body = text[opening + len("```python"):text.index("```", opening + 3)]
    namespace: dict = {}
    exec(compile(body, str(SKILL), "exec"), namespace)
    return namespace


def _answering_fake(fake) -> None:
    """A Bot API that answers by method, and delivers a reply once asked."""
    asked: list[int] = []
    delivered: list[bool] = []

    def answer(recorded) -> tuple[int, bytes]:
        if recorded.method == "sendMessage":
            asked.append(4242)
            return 200, json.dumps({"ok": True, "result": {"message_id": 4242}}).encode()
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
            "TELEGRAM_HITL_PORT": "0",
            "TELEGRAM_BOT_TOKEN": "42:end-to-end",
            "PYTHONPATH": str(Path(claude_config.__file__).resolve().parents[1]),
        },
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    try:
        deadline = time.monotonic() + 20
        while not (state / "port").exists() and time.monotonic() < deadline:
            time.sleep(0.05)
        assert (state / "port").exists(), "the proxy never bound a port"
        yield process, state, int((state / "port").read_text())
    finally:
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()


def test_a_whole_cycle_runs_through_the_real_process(proxy_process) -> None:
    process, state, port = proxy_process
    log = state / "channel.jsonl"
    records = _recipe("read-log")["records"]
    answer_to = _recipe("answers")["answer_to"]
    inbound_state = _recipe("health")["inbound_state"]
    topics = _recipe("topics")["topics"]

    def call(method: str, payload: dict) -> dict:
        request = urllib.request.Request(
            f"http://127.0.0.1:{port}/{method}", data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json", "X-Session-Id": "end-to-end"},
            method="POST")
        with urllib.request.urlopen(request, timeout=10) as answer:
            return json.loads(answer.read())

    assert inbound_state(records(log)) == "up"

    topic = call("createForumTopic", {"chat_id": -100, "name": "research: alpha"})
    thread = topic["result"]["message_thread_id"]
    asked = call("sendMessage", {"chat_id": -100, "message_thread_id": thread,
                                 "text": "Ship it?"})

    deadline = time.monotonic() + 20
    found = None
    while found is None and time.monotonic() < deadline:
        found = answer_to(records(log), asked["result"]["message_id"])
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
```

- [x] **Step 2: Run it**

Run: `cd /root/claude-config-work2 && uv run pytest tests/test_telegram_hitl_end_to_end.py -q`
Expected: 1 passed

- [x] **Step 3: Run the whole suite**

Run: `cd /root/claude-config-work2 && uv run pytest tests/ -q 2>&1 | tail -3`
Expected: `399 passed` — 398 plus this one.

- [x] **Step 4: Commit**

```bash
cd /root/claude-config-work2
git add tests/test_telegram_hitl_end_to_end.py
git commit -m "test(telegram-hitl): one whole cycle through the real process"
```

### Task 8: Live verification

Not a test: it needs the real token, the real group, and a human at a phone. Run
it once, at the end. Until this branch merges, substitute the worktree path for
`/repos/claude-config` in the `--project` flag.

- [x] **Step 1: Confirm nothing else is polling**

The invariant is exactly one drain, and a newcomer seizes the stream rather than
being refused. The first-party `telegram` plugin and `telegram-bot-skill` each
start their own poller.

Run: `pgrep -af "telegram|bridge" | grep -v pgrep`
Expected: no output. If anything is listed, stop it before continuing.

- [x] **Step 2: Record the chat id**

```bash
mkdir -p ~/.claude/channels/telegram-hitl
echo -1004384191085 > ~/.claude/channels/telegram-hitl/chat_id
```

That is `claude-channel-group`, verified as a forum with the bot holding
`can_manage_topics`. If Topics is ever re-enabled on a fresh group the id
changes — follow `migrate_to_chat_id`.

- [x] **Step 3: Start the proxy**

```bash
UV_PROJECT_ENVIRONMENT=$HOME/.claude/venvs/claude-config \
agent-tools run --background --desc "telegram-hitl proxy" \
  uv run --project /repos/claude-config python -m claude_config.telegram_hitl
```

Expected: a capture directory and pids. The capture's `output` holds one line:
`telegram-hitl: 127.0.0.1:18420 -> /root/.claude/channels/telegram-hitl/channel.jsonl`

- [x] **Step 4: Confirm the bot answers and the denylist bites**

```bash
curl -s http://127.0.0.1:18420/getMe
curl -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1:18420/getUpdates
```

Expected: `"username":"claude_channel_bot"` in the first, `403` from the second.

- [x] **Step 5: Confirm the chat is still a forum**

```bash
curl -s "http://127.0.0.1:18420/getChat?chat_id=$(cat ~/.claude/channels/telegram-hitl/chat_id)" \
  | python3 -c 'import json,sys; c=json.load(sys.stdin)["result"]; print(c["type"], c.get("is_forum"))'
```

Expected: `supergroup True`

- [x] **Step 6: Create a topic and ask a question**

```bash
CHAT=$(cat ~/.claude/channels/telegram-hitl/chat_id)
THREAD=$(curl -s -X POST http://127.0.0.1:18420/createForumTopic \
  -H 'Content-Type: application/json' \
  -d "{\"chat_id\": $CHAT, \"name\": \"hitl smoke test\"}" \
  | python3 -c 'import json,sys; print(json.load(sys.stdin)["result"]["message_thread_id"])')
curl -s -X POST http://127.0.0.1:18420/sendMessage \
  -H 'Content-Type: application/json' -H "X-Session-Id: smoke" \
  -d "{\"chat_id\": $CHAT, \"message_thread_id\": $THREAD, \"text\": \"Reply to this message with anything.\"}" \
  | python3 -c 'import json,sys; print("message_id", json.load(sys.stdin)["result"]["message_id"])'
```

Expected: a thread id, then a message id. The message appears in the group under
its own topic.

- [x] **Step 7: Reply from the phone, as a reply to that message**

- [x] **Step 8: Confirm the answer is in the log, self-describing**

```bash
python3 -c '
import json
path = "/root/.claude/channels/telegram-hitl/channel.jsonl"
for line in open(path, "rb"):
    if not line.endswith(b"\n"):
        break
    record = json.loads(line)
    if record["kind"] == "inbound":
        message = record["update"].get("message") or {}
        print(message.get("message_id"), "thread", message.get("message_thread_id"),
              "is_topic", message.get("is_topic_message"),
              "replies_to", (message.get("reply_to_message") or {}).get("message_id"),
              repr(message.get("text")))
'
```

Expected: one line per inbound message, the reply showing `is_topic True`, the
thread from Step 5, and `replies_to` equal to the message id from Step 5.

- [x] **Step 9: Acknowledge it, and remove the smoke-test topic**

Both ids come out of the log, so this step needs nothing carried over from an
earlier shell.

```bash
LOG=~/.claude/channels/telegram-hitl/channel.jsonl
CHAT=$(cat ~/.claude/channels/telegram-hitl/chat_id)
THREAD=$(python3 -c '
import json, sys
last = None
for line in open(sys.argv[1], "rb"):
    if not line.endswith(b"\n"): break
    record = json.loads(line)
    if (record["kind"] == "outbound" and record["method"] == "createForumTopic"
            and record["response"].get("ok")):
        last = record["response"]["result"]["message_thread_id"]
print(last)' "$LOG")
REPLY=$(python3 -c '
import json, sys
last = None
for line in open(sys.argv[1], "rb"):
    if not line.endswith(b"\n"): break
    record = json.loads(line)
    if record["kind"] == "inbound":
        message = record["update"].get("message") or {}
        if message.get("reply_to_message"): last = message["message_id"]
print(last)' "$LOG")
echo "thread $THREAD, reply $REPLY"

curl -s -X POST http://127.0.0.1:18420/setMessageReaction \
  -H 'Content-Type: application/json' \
  -d "{\"chat_id\": $CHAT, \"message_id\": $REPLY, \"reaction\": [{\"type\":\"emoji\",\"emoji\":\"👍\"}]}"
curl -s -X POST http://127.0.0.1:18420/deleteForumTopic \
  -H 'Content-Type: application/json' \
  -d "{\"chat_id\": $CHAT, \"message_thread_id\": $THREAD}"
```

Expected: the thread and reply ids, then `{"ok":true,"result":true}` twice. The
reaction is visible on the phone before the topic goes.

- [x] **Step 10: Confirm the channel reports itself healthy, then stop it**

```bash
grep -c '"kind": "fault"' ~/.claude/channels/telegram-hitl/channel.jsonl
kill "$(cat ~/.claude/channels/telegram-hitl/proxy.lock)"
sleep 1; tail -1 ~/.claude/channels/telegram-hitl/channel.jsonl
```

Expected: `0` faults (grep exits 1 when it counts none, which is the wanted
answer here); then the last record is
`{"kind": "proxy", "event": "stopped", "reason": "SIGTERM"}`. The lock file holds
the pid, which is what makes the `kill` safe to run without hunting for it.

---

## Self-review

Run after the last task, against
`docs/superpowers/specs/2026-09-12-telegram-hitl-design.md`:

| Spec claim | Where it is held to account |
| --- | --- |
| Inbound is exclusive and the incumbent loses | `test_a_second_proxy_refuses_to_start_and_leaves_the_first_serving` |
| Outbound needs no coordination | `test_concurrent_senders_all_succeed_and_are_all_logged` |
| Inbound records are self-describing | `test_the_answer_finder_matches_the_reply_to_a_question`, Task 8 Step 8 |
| Reactions work, with a restricted alphabet | Task 5 traps, Task 8 Step 9 |
| The proxy interprets nothing | `test_a_send_reaches_telegram_unchanged`, `test_a_get_is_forwarded_as_a_get_with_its_query` |
| Limits are diagnosed, not absorbed | `test_an_error_reaches_the_caller_verbatim` |
| The denylist is derived from the invariants | `test_a_denied_method_never_reaches_telegram`, `test_every_denied_method_states_why` |
| The denylist cannot be walked past by respelling the method | `test_a_denied_method_cannot_be_reached_by_respelling_it` |
| A send is forwarded whole or refused, never silently emptied | `test_a_chunked_body_is_refused_rather_than_forwarded_empty` |
| An upstream that hangs or garbles is a logged fault, not a dead component | `test_an_upstream_that_never_answers_is_reported_and_logged`, `test_a_handler_that_raises_is_recorded_rather_than_lost` |
| Errors are logged, not just returned | `test_an_unreachable_telegram_is_reported_and_logged`, the drain fault tests, `test_startup_and_shutdown_leave_a_record` |
| Log transitions, not occurrences | `test_repeated_faults_log_one_transition_then_one_clearance` |
| The log is the topic registry | `test_the_topic_registry_is_reconstructed_from_the_log` |
| Durability ordering | `test_the_log_is_written_before_telegram_is_told_to_forget` |
| The drain does nothing else | `drain.py` has no call but `getUpdates`; `test_a_failure_to_record_is_fatal` |
| A misconfigured start fails loudly instead of presenting as a quiet channel | `test_a_misconfigured_token_stops_the_process_loudly`, `test_a_start_that_fails_is_recorded_too` |
| The lock is the descriptor, not the file a dead process left behind | `test_a_stale_lock_file_does_not_block_a_start` |
| A down channel is distinguishable from a slow human | `test_the_inbound_state_distinguishes_a_dead_channel_from_a_quiet_one`, `test_a_crashing_drain_records_why_it_stopped` |
| A blipping channel is not mistaken for a dead one | the same test's `blip` case — found live, where one reset cleared in 26s |
| The agent decides topics | Task 5, stated as judgement with no mechanism behind it |
| The traps must not be lost | `test_the_skill_still_carries_every_trap_that_cost_time` |
| The skill does not drift from what the proxy actually answers | `test_the_skill_documents_every_refusal_the_proxy_returns` |
| The skill's examples name variables that exist | `test_the_skill_names_the_session_variable_that_exists` |
| The layers fit, and the recipes work on what the proxy really writes | `test_a_whole_cycle_runs_through_the_real_process` |
| The fault channel survives concurrent reporters | `test_concurrent_reporters_log_one_transition_per_episode` (fails 5/5 runs without the lock) |
| One failed write does not make the log unreadable | `test_a_short_write_raises_and_bounds_the_damage_to_one_line`, `test_the_log_reader_surfaces_a_damaged_line_and_keeps_going` |
| A blanked or shell-style token file fails locally, not at Telegram | `test_an_empty_token_value_is_treated_as_missing`, `test_an_export_prefix_is_accepted`, `test_the_last_assignment_wins` |
