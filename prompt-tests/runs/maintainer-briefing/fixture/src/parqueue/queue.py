from __future__ import annotations

import json
import os
from pathlib import Path


class Queue:
    """A work queue backed by one directory of JSON files."""

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def put(self, payload: dict) -> str:
        name = f"{os.urandom(8).hex()}.json"
        (self.root / name).write_text(json.dumps(payload))
        return name

    def drain(self) -> list[dict]:
        out = []
        for p in sorted(self.root.glob("*.json")):
            out.append(json.loads(p.read_text()))
            p.unlink()
        return out
