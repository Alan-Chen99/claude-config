"""The release-notes reader must find the end of the literal, not a quote in it.

`changelog.py` slices one JS string literal out of the decompiled binary and
decodes it. Getting the closing quote wrong does not degrade: the slice either
stops early (truncated notes) or runs into unrelated JS, and the runbook step
that reads it is the one that names the *reason* behind every other diff. The
quote style is the minifier's -- 2.1.269 wrote the literal double-quoted,
2.1.289 single-quoted -- so both forms are exercised.
"""

import importlib.util
from pathlib import Path
from types import ModuleType

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / ".claude" / "skills" / "update-claude-code" / "changelog.py"


def _changelog() -> ModuleType:
    """Import the script from a directory that is not on `pythonpath`."""
    spec = importlib.util.spec_from_file_location("changelog", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize(
    "literal",
    [
        '""',
        '"plain"',
        r'"an escaped \" quote"',
        r'"a trailing backslash \\"',
        r'"both \" and \\"',
        r'"\\\\"',
        r'"## 2.1.269\n- a note ending in a path C:\\"',
        "''",
        r"""'it\'s single-quoted, with a "double" inside'""",
        r"'## 2.1.287\n- a trailing backslash \\'",
    ],
)
def test_literal_end_finds_the_closing_quote(literal: str) -> None:
    # Padded so an overshoot has somewhere to run to, which is the whole
    # failure mode: without padding a wrong answer still lands on the last
    # character and looks right.
    prefix = "var x="
    src = f"{prefix}{literal};var y=\"unrelated\";"
    start = len(prefix)
    assert _changelog()._literal_end(src, start) == start + len(literal) - 1


@pytest.mark.parametrize(
    ("literal", "text"),
    [
        (r'"## 2.1.269\n- \u2014 dash"', "## 2.1.269\n- \u2014 dash"),
        (r"""'## 2.1.287\n- it\'s "quoted" \ud83d\ude00'""", "## 2.1.287\n- it's \"quoted\" \U0001f600"),
        (r"'tab\there, slash \/ kept, backslash \\'", "tab\there, slash / kept, backslash \\"),
    ],
)
def test_decode_resolves_js_escapes_under_either_quote(literal: str, text: str) -> None:
    assert _changelog()._decode(literal) == text


def test_release_notes_still_parse_from_the_installed_decompile() -> None:
    src_dir = _changelog().DEFAULT_SRC
    if not src_dir.is_dir():
        pytest.skip(f"no decompiled tree at {src_dir}")
    text = _changelog().changelog(src_dir)
    assert text.startswith("## ")
    assert "\n## " in text  # more than one release in the window
