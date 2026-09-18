"""The captured built-in skill bodies must still agree with their manifest.

`docs/system-prompt-snapshot/builtin-skills/` is read as a diff across a Claude
Code release, so a body that no longer matches the hash beside it shows a delta
nobody captured. The bodies also carry absolute paths that differ on every run;
those are normalized at capture time, and a leaked one would show up in the diff
of every future capture as noise that looks like a real change.

Regenerate with `docs/system-prompt-snapshot/capture_skills.py`.
"""

import hashlib
import importlib.util
import json
import re
import sys
from pathlib import Path
from types import ModuleType

import pytest

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT = ROOT / "docs" / "system-prompt-snapshot"
SKILLS_DIR = SNAPSHOT / "builtin-skills"
MANIFEST = SKILLS_DIR / "manifest.json"

# Every shape capture_skills._classify can assign. A new one reaching the
# manifest without this list being updated is a capture whose meaning nobody
# has written down.
SHAPES = {"body", "stub", "forked", "local-exec", "unavailable", "none"}

# Paths that differ between two captures of the same release. `_normalize`
# replaces each; any survivor here would make every later diff noisy.
VOLATILE = (
    re.compile(r"/bundled-skills/\d+\.\d+\.\d+/[0-9a-f]{8,}"),
    re.compile(r"/tmp/capture-cwd-\w+"),
    re.compile(r"/tmp/claude-\d+/"),
)


def _capture_skills() -> ModuleType:
    """Import the capture script, which is not on `pythonpath`."""
    spec = importlib.util.spec_from_file_location(
        "capture_skills", SNAPSHOT / "capture_skills.py"
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _manifest() -> dict:
    return json.loads(MANIFEST.read_text())


def test_manifest_exists() -> None:
    # Guards the parametrized tests below: with no manifest they collapse to
    # skips, and a bare pytest exit code cannot tell that from a pass.
    assert MANIFEST.exists(), f"{MANIFEST} missing; run capture_skills.py"
    assert _manifest()["skills"], "manifest lists no skills"


def test_manifest_covers_the_captured_roster() -> None:
    """Every built-in skill the snapshot advertises has a manifest entry.

    The roster comes from the capture's own skill listing, so a release that
    adds a built-in skill fails here until it is captured, rather than being
    quietly absent from the directory.
    """
    roster = _capture_skills().builtin_skill_names(
        SNAPSHOT / "opus-5" / "default" / "request.json"
    )
    assert set(roster) == set(_manifest()["skills"]), (
        "manifest and the captured skill listing disagree; "
        "run capture_skills.py"
    )


@pytest.mark.parametrize("name", sorted(_manifest()["skills"]) if MANIFEST.exists() else [])
def test_body_matches_manifest(name: str) -> None:
    entry = _manifest()["skills"][name]
    assert entry["shape"] in SHAPES, f"{name}: unknown shape {entry['shape']!r}"

    path = SKILLS_DIR / f"{name}.md"
    if not entry.get("chars"):
        # A skill that delivers nothing is recorded by its reason, not by an
        # empty file that would read as a capture failure.
        assert not path.exists(), f"{name}: manifest says no body but {path} exists"
        assert entry.get("note"), f"{name}: no body captured and no reason given"
        return

    assert path.exists(), f"{name}: manifest records a body but {path} is missing"
    text = path.read_text()
    assert len(text) == entry["chars"], f"{name}: size differs from the manifest"
    assert hashlib.sha256(text.encode()).hexdigest() == entry["sha256"], (
        f"{name}: {path.name} no longer matches its manifest hash"
    )


@pytest.mark.parametrize("path", sorted(SKILLS_DIR.glob("*.md")) if SKILLS_DIR.is_dir() else [])
def test_no_volatile_paths_survive(path: Path) -> None:
    text = path.read_text()
    for pattern in VOLATILE:
        assert not pattern.search(text), (
            f"{path.name} still carries a per-run path matching {pattern.pattern}; "
            "capture_skills._normalize needs to cover it"
        )


@pytest.mark.parametrize("path", sorted(SKILLS_DIR.glob("*.md")) if SKILLS_DIR.is_dir() else [])
def test_no_harness_text_captured_as_a_body(path: Path) -> None:
    """A body must be the skill, not something else the session carried.

    The extractor picks the longest injected block, and a session carries text
    that competes with a skill body on length: Claude Code's type-ahead
    suggester runs against the same pid and carries tools, and on opus the
    system reminders arrive untagged. Both have been captured as bodies.
    """
    module = _capture_skills()
    head = path.read_text()[:200]
    leaked = next(
        (m for m in module._AUXILIARY + module._WRAPPERS if m in head), None
    )
    assert leaked is None, (
        f"{path.name} opens with {leaked!r}, which is harness text, not the skill"
    )


def test_normalize_replaces_a_real_extraction_path() -> None:
    """Staged rather than asserted against a capture that may not contain one.

    Only skills shipping resource files get a `Base directory` line, so a
    regression here is invisible on a run where none of them were captured.
    """
    module = _capture_skills()
    raw = (
        "Base directory for this skill: "
        "/tmp/claude-0/bundled-skills/2.1.269/8b5b3624970e774f049f2f106391de3f/claude-api\n\n"
        "# Body\n"
    )
    text, changed = module._normalize(raw)
    assert changed
    assert "<bundled-skills-dir>" in text
    assert "8b5b3624" not in text
