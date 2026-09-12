"""The append-only JSONL channel log: the system's only read interface.

Many processes append here at once, so every record is one O_APPEND write
syscall — the kernel then orders whole records and no two can interleave.
Each write is fsynced because the drain's durability ordering depends on a
record being on disk before Telegram is told to forget the update.
"""

import json
import os
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
            raise OSError(f"short write to channel log: {written} of {len(line)} bytes")
        os.fsync(self._fd)

    def close(self) -> None:
        os.close(self._fd)


class ErrorTransitions:
    """Log entering and leaving a failing state, not every occurrence.

    A stolen update stream fails every poll, and recording each one at poll rate
    would bury the log in identical lines. The interesting events are the edges.
    """

    def __init__(self, log: ChannelLog, source: str) -> None:
        self._log = log
        self._source = source
        self._signature: str | None = None
        self._count = 0

    def failed(self, signature: str, detail: str) -> None:
        if signature == self._signature:
            self._count += 1
            return
        self.ok()
        self._signature = signature
        self._count = 1
        self._log.append({"kind": "fault", "source": self._source, "state": "failing",
                          "signature": signature, "detail": detail})

    def ok(self) -> None:
        """No-op while healthy, so a working component writes nothing."""
        if self._signature is None:
            return
        self._log.append({"kind": "fault", "source": self._source, "state": "cleared",
                          "signature": self._signature, "occurrences": self._count})
        self._signature = None
        self._count = 0
