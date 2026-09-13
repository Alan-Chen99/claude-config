"""The tracked snapshot rendering must still agree with the request beside it.

`docs/system-prompt-snapshot/**/prompt.md` and `tools/*.md` are rendered from
the `request.json` in the same directory. They are what a reviewer diffs across
a Claude Code release, so a stale one is worse than none: it shows a delta the
model was never sent, and it shows it in the file the runbook sends the reader
to. Re-render with `render_capture.py --tree docs/system-prompt-snapshot`.
"""

import importlib.util
import json
from pathlib import Path
from types import ModuleType

import pytest

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT = ROOT / "docs" / "system-prompt-snapshot"


def _render_capture() -> ModuleType:
    """Import the renderer from a directory that is not on `pythonpath`."""
    global _MODULE
    if _MODULE is None:
        spec = importlib.util.spec_from_file_location(
            "render_capture", SNAPSHOT / "render_capture.py"
        )
        assert spec and spec.loader
        _MODULE = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(_MODULE)
    return _MODULE


_MODULE: ModuleType | None = None

# The renderer's own discovery, so this file cannot find a capture the renderer
# would not: the gitignored `capture-output/` holds a real `request.json`, and
# a bare rglob would verify its render against itself.
CAPTURES = _render_capture().find_captures(SNAPSHOT)


def test_captures_exist() -> None:
    # Guards the two parametrized tests below: an empty CAPTURES list turns
    # them into skips, and a bare `pytest` exit code cannot tell an all-skipped
    # run from a passing one.
    assert len(CAPTURES) >= 13


def test_discovery_excludes_working_directories(monkeypatch: pytest.MonkeyPatch) -> None:
    """The scratch `regenerate.py` writes into must never be read as a capture.

    Staged rather than skipped-if-absent: a machine that has never captured is
    where the bug looks fixed.
    """
    monkeypatch.chdir(ROOT)  # so the relative spelling below is expressible
    scratch = SNAPSHOT / "capture-output"
    request = scratch / "request.json"
    had_dir, had_file = scratch.is_dir(), request.exists()
    try:
        scratch.mkdir(exist_ok=True)
        if not had_file:
            request.write_text("{}")
        for root in (SNAPSHOT, SNAPSHOT.relative_to(ROOT)):
            # Both spellings: `--tree` is invoked with a relative root, and an
            # unresolved relative path asks git about a doubled path.
            found = _render_capture().find_captures(root)
            assert request.exists()  # the thing discovery must decline to return
            assert request.resolve() not in [f.resolve() for f in found], root
            assert len(found) >= 13, root
    finally:
        if not had_file and request.exists():
            request.unlink()
        if not had_dir and scratch.is_dir():
            scratch.rmdir()


@pytest.mark.parametrize("request_path", CAPTURES, ids=lambda p: str(p.parent.relative_to(SNAPSHOT)))
def test_tracked_rendering_matches_request(request_path: Path, tmp_path: Path) -> None:
    request = json.loads(request_path.read_text())
    _render_capture().write_capture(request, tmp_path)

    tracked = request_path.parent
    assert (tmp_path / "prompt.md").read_text() == (tracked / "prompt.md").read_text()

    expected = {p.name for p in (tmp_path / "tools").glob("*.md")}
    assert {p.name for p in (tracked / "tools").glob("*.md")} == expected
    for name in sorted(expected):
        assert (tmp_path / "tools" / name).read_text() == (
            tracked / "tools" / name
        ).read_text(), name


@pytest.mark.parametrize("request_path", CAPTURES, ids=lambda p: str(p.parent.relative_to(SNAPSHOT)))
def test_rendering_drops_nothing(request_path: Path) -> None:
    """Every captured string reaches a rendered file.

    Byte-equality above only says the tracked files are what the renderer
    produces today; it would still hold if the renderer quietly stopped
    emitting a block shape a future release introduces.
    """
    request = json.loads(request_path.read_text())
    captured = request_path.parent
    prompt = (captured / "prompt.md").read_text()

    texts = [b for b in request.get("system", []) if b.get("type") == "text"]
    for message in request.get("messages", []):
        content = message["content"]
        blocks = [{"type": "text", "text": content}] if isinstance(content, str) else content
        texts += [b for b in blocks if b.get("type") == "text"]
    for block in texts:
        assert block["text"] in prompt

    for tool in request.get("tools", []):
        body = (captured / "tools" / f"{tool['name']}.md").read_text()
        assert tool.get("description", "") in body
        assert json.dumps(tool.get("input_schema", {}), indent=2, ensure_ascii=False) in body
        attrs = {k: v for k, v in tool.items() if k not in ("name", "description", "input_schema")}
        if attrs:
            assert json.dumps(attrs, indent=2, ensure_ascii=False) in body
        # Order is a property of the request, not of the directory listing.
        assert f"- `{tool['name']}`" in prompt

    params = {k: v for k, v in request.items() if k not in ("tools", "system", "messages")}
    assert json.dumps(params, indent=2, ensure_ascii=False) in prompt
