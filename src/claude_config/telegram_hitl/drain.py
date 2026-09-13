"""The single getUpdates consumer: poll, append, flush, advance. Nothing else.

Any other work here is work that can kill the one component nothing else can
replace — a newcomer cannot simply be started alongside it, because a second
consumer evicts the first. A dead drain reaches a waiting session as "the human
has not answered yet", which is the failure this whole design exists to prevent.

Its failure surface is therefore held to two cases: a failed poll, which it
retries, and a failure to durably record an update, which is fatal because
continuing past it would silently drop a human's answer.
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
                # Raised into this handler deliberately: a result that is not a
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
            offset = update["update_id"] + 1
        if updates:
            write_offset(offset_path, offset)


def _pause(stop: threading.Event, backoff: float, cap: float) -> float:
    """Wait out the backoff, returning the next one. Interruptible by `stop`."""
    stop.wait(backoff)
    return min(backoff * 2, cap)
