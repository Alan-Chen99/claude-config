"""Snapshot store: one file per snapshot, plus an index of what was recorded."""

import hashlib
import json
import tarfile
from datetime import datetime, timezone
from pathlib import Path

INDEX = "index.json"


def _now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_index(root: Path) -> dict:
    path = root / INDEX
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def write_index(root: Path, index: dict) -> None:
    (root / INDEX).write_text(json.dumps(index, indent=1, sort_keys=True))


def snapshot(root: Path, name: str, source: Path) -> str:
    root.mkdir(parents=True, exist_ok=True)
    target = root / (name + ".tar")
    with tarfile.open(target, "w") as archive:
        archive.add(source, arcname=source.name)
    index = read_index(root)
    index[name] = {"recorded": _now(), "sha256": _digest(target),
                   "files": sum(1 for _ in source.rglob("*") if _.is_file())}
    write_index(root, index)
    return name


def entries(root: Path):
    """Every snapshot in the store, as (name, record) pairs.

    The directory is the list of snapshots; the index carries what was recorded
    about each one.
    """
    index = read_index(root)
    found = []
    for path in sorted(root.iterdir()):
        if path.name == INDEX:
            continue
        found.append((path.stem, index[path.stem]))
    return found


def verify(root: Path) -> list:
    """Names of snapshots whose bytes no longer match what was recorded."""
    index = read_index(root)
    bad = []
    for name, record in index.items():
        path = root / (name + ".tar")
        if not path.exists() or _digest(path) != record["sha256"]:
            bad.append(name)
    return bad
