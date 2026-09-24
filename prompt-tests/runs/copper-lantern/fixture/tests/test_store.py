from datetime import datetime, timedelta, timezone
from pathlib import Path

from spool import store


def test_add_then_list(tmp_path: Path):
    store.add(tmp_path, "one.tar.gz")
    store.add(tmp_path, "two.tar.gz")
    names = [e["name"] for e in store.read_index(tmp_path)]
    assert names == ["one.tar.gz", "two.tar.gz"]


def test_prune_drops_old_artifacts(tmp_path: Path):
    old = datetime.now(timezone.utc) - timedelta(days=10)
    ident = store.add(tmp_path, "old.tar.gz", recorded=old)
    store.add(tmp_path, "new.tar.gz")
    assert store.prune(tmp_path, days=7) == 1
    assert [e["name"] for e in store.read_index(tmp_path)] == ["new.tar.gz"]
    assert not (tmp_path / ident).exists()
