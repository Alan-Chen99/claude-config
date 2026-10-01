"""`settings.json` must already be in the order Claude Code writes it in.

Claude Code writes the *validated* settings object on any UI change, so the
file comes back in the settings schema's declaration order and a hand-ordered
file is reverted the next time the user touches `/config` — as a 12-key
reordering sitting on top of whatever that commit was actually about. These
pin the two halves of "already in that order": the byte format, which needs no
decompile, and the key order, re-derived from the binary so a release that
reorders the schema fails here instead of being discovered as churn.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from types import ModuleType

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / ".claude" / "skills" / "update-claude-code" / "settings-order.py"
SETTINGS = ROOT / "settings.json"
DECOMPILED = Path("/repos/claude-code-decompiled/src")


def _module() -> ModuleType:
    """Import the script from a directory that is not on `pythonpath`."""
    spec = importlib.util.spec_from_file_location("settings_order", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_settings_json_is_byte_identical_to_what_claude_code_would_write() -> None:
    """`JSON.stringify(U, null, 2) + "\\n"` (`chunk-2x9ed96k.js:3096`).

    Independent of the key order and of any decompile: two-space indent,
    non-ASCII left unescaped, exactly one trailing newline. Drift in any of
    them makes cc rewrite the whole file on the next setting change.
    """
    raw = SETTINGS.read_text()
    assert raw == json.dumps(json.loads(raw), indent=2, ensure_ascii=False) + "\n"


@pytest.mark.skipif(not DECOMPILED.is_dir(), reason="decompiled Claude Code not present")
def test_settings_json_key_order_matches_the_live_settings_schema() -> None:
    """Fails when the file is hand-ordered, and when a release moves a key.

    Both remedies are the same command, and which one it is shows in the diff:
    `settings-order.py --write`.
    """
    order, _ = _module().derive_order(DECOMPILED)
    rank = {key: index for index, key in enumerate(order)}
    keys = list(json.loads(SETTINGS.read_text()))

    unplaceable = [key for key in keys if key not in rank]
    assert not unplaceable, (
        f"not in the 2.1.269 settings schema: {unplaceable}. Either the key is "
        "gone from this build, or it comes from the runtime `...Ks(e)` spread — "
        "read the position cc wrote out of the file rather than deriving it."
    )
    assert keys == sorted(keys, key=lambda key: rank[key])


@pytest.mark.skipif(not DECOMPILED.is_dir(), reason="decompiled Claude Code not present")
def test_the_derived_order_is_the_whole_schema() -> None:
    """The floor that separates "read every key" from "read four of them".

    A reworded anchor or a re-indented schema makes the scan return a short
    list, and a short list satisfies the order assertion vacuously — every key
    it does not know about is simply not checked.
    """
    order, _ = _module().derive_order(DECOMPILED)
    assert len(order) >= 120
    # The first and last entries of the literal: a window that slipped at either
    # end would still clear the floor.
    assert order[0] == "$schema"
    assert "theme" in order and "cleanupPeriodDays" in order


def test_a_collapsed_extraction_exits_two_rather_than_returning_a_short_list(
    tmp_path: Path,
) -> None:
    """No tree, no anchor, and an unterminated schema are all exit 2."""
    module = _module()

    with pytest.raises(SystemExit) as absent:
        module.derive_order(tmp_path / "nonexistent")
    assert absent.value.code == 2

    (tmp_path / "chunk-aaaa.js").write_text("var x = 1;\n")
    with pytest.raises(SystemExit) as anchorless:
        module.derive_order(tmp_path)
    assert anchorless.value.code == 2

    (tmp_path / "chunk-bbbb.js").write_text(module.ANCHOR + "\n    theme: o(),\n")
    with pytest.raises(SystemExit) as unclosed:
        module.derive_order(tmp_path)
    assert unclosed.value.code == 2
