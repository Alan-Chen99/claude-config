from pathlib import Path

from warden import store


def _tree(tmp_path: Path) -> Path:
    source = tmp_path / "src"
    source.mkdir()
    (source / "a.txt").write_text("alpha")
    (source / "b.txt").write_text("bravo")
    return source


def test_snapshot_then_list(tmp_path: Path):
    root = tmp_path / "snapshots"
    store.snapshot(root, "nightly", _tree(tmp_path))
    names = [name for name, _ in store.entries(root)]
    assert names == ["nightly"]


def test_verify_notices_a_changed_snapshot(tmp_path: Path):
    root = tmp_path / "snapshots"
    store.snapshot(root, "nightly", _tree(tmp_path))
    assert store.verify(root) == []
    (root / "nightly.tar").write_bytes(b"not a tar")
    assert store.verify(root) == ["nightly"]
