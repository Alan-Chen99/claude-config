"""Read and write a ledger store file."""

import json
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_STORE = Path("sample-store.json")


def load(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return json.loads(path.read_text())


def append(path: Path, text: str) -> dict:
    entries = load(path)
    entry = {"at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "text": text}
    entries.append(entry)
    path.write_text(json.dumps(entries, indent=2) + "\n")
    return entry
