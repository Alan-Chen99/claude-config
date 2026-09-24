from pathlib import Path

from ledger import store


def test_append_then_load_round_trips(tmp_path: Path) -> None:
    path = tmp_path / "s.json"
    store.append(path, "first")
    store.append(path, "second")
    entries = store.load(path)
    assert [e["text"] for e in entries] == ["first", "second"]


def test_load_missing_store_is_empty(tmp_path: Path) -> None:
    assert store.load(tmp_path / "nothing.json") == []
