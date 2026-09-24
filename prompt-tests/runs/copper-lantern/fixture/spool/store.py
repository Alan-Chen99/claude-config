"""Artifact spool: one file per artifact, plus a line-per-artifact index."""

import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

INDEX = "index.jsonl"


def _now():
    return datetime.now(timezone.utc)


def _stamp(moment):
    return moment.strftime("%Y-%m-%dT%H:%M:%SZ")


def read_index(root: Path):
    path = root / INDEX
    if not path.exists():
        return []
    entries = []
    for line in path.read_text().splitlines():
        if line.strip():
            entries.append(json.loads(line))
    return entries


def add(root: Path, name: str, recorded=None):
    root.mkdir(parents=True, exist_ok=True)
    recorded = recorded or _now()
    ident = "%06x" % (abs(hash((name, _stamp(recorded)))) % 0xFFFFFF)
    (root / ident).write_text(name)
    entry = {"id": ident, "recorded": _stamp(recorded), "name": name}
    with (root / INDEX).open("a") as handle:
        handle.write(json.dumps(entry) + "\n")
    return ident


def prune(root: Path, days: int):
    cutoff = _now() - timedelta(days=days)
    keep, drop = [], []
    for entry in read_index(root):
        recorded = datetime.strptime(entry["recorded"], "%Y-%m-%dT%H:%M:%SZ").replace(
            tzinfo=timezone.utc
        )
        (drop if recorded < cutoff else keep).append(entry)
    for entry in drop:
        artifact = root / entry["id"]
        if artifact.exists():
            artifact.unlink()
    tmp = root / (INDEX + ".tmp")
    tmp.write_text("".join(json.dumps(e) + "\n" for e in keep))
    os.replace(tmp, root / INDEX)
    return len(drop)
