#!/usr/bin/env python3
"""Drain the job queue, one render per id."""
import fcntl
import subprocess
import sys
from pathlib import Path

CACHE = Path("cache")
QUEUE = Path("queue.txt")


def source_is_complete(upload_id: str) -> bool:
    """The upload handler holds this lock while it writes the decoded source."""
    path = CACHE / f"{upload_id}.raw"
    if not path.exists():
        return False
    with open(path, "rb") as fh:
        fcntl.flock(fh, fcntl.LOCK_SH)
        try:
            return fh.seek(0, 2) > 0
        finally:
            fcntl.flock(fh, fcntl.LOCK_UN)


def main() -> None:
    for line in QUEUE.read_text().splitlines():
        upload_id = line.strip()
        if not upload_id:
            continue
        if not source_is_complete(upload_id):
            print(f"skip {upload_id}: source not ready", file=sys.stderr)
            continue
        subprocess.run([sys.executable, "render.py", upload_id], check=True)


if __name__ == "__main__":
    main()
