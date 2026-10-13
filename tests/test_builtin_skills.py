"""The captured built-in skill bodies must still agree with their manifest.

`docs/system-prompt-snapshot/builtin-skills/` is read as a diff across a Claude
Code release, so a body or extracted file that no longer matches the hash beside
it shows a delta nobody captured. The bodies also carry absolute paths that
differ on every run; those are normalized at capture time, and a leaked one would
show up in the diff of every future capture as noise that looks like a real change.

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
    re.compile(r"capture-cwd-\w+"),
    re.compile(r"/tmp/claude-\d+/"),
    re.compile(r"/dev-mods/(?!<session-id>)"),
)

# What each skill's extraction directory held, mirrored under builtin-skills/<name>/.
BUNDLE_FILES = (
    sorted(p for p in SKILLS_DIR.glob("*/**/*") if p.is_file()) if SKILLS_DIR.is_dir() else []
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


def _with_files() -> dict[str, dict]:
    return {n: e["files"] for n, e in _manifest()["skills"].items() if e.get("files")}


@pytest.mark.parametrize("name", sorted(_with_files()) if MANIFEST.exists() else [])
def test_bundle_files_match_manifest(name: str) -> None:
    files = _with_files()[name]
    root = SKILLS_DIR / name
    on_disk = sorted(p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file())
    assert on_disk == sorted(files), f"{name}/ and its manifest entry list different files"
    for rel, meta in files.items():
        data = (root / rel).read_bytes()
        assert len(data) == meta["bytes"], f"{name}/{rel}: size differs from the manifest"
        assert hashlib.sha256(data).hexdigest() == meta["sha256"], (
            f"{name}/{rel} no longer matches its manifest hash"
        )


def test_every_bundle_directory_belongs_to_a_skill_with_files() -> None:
    """A directory left behind by a skill that no longer ships files, or by one
    the roster dropped, would read as files the release still ships."""
    dirs = {p.name for p in SKILLS_DIR.iterdir() if p.is_dir()}
    assert dirs == set(_with_files())


@pytest.mark.parametrize(
    "name",
    sorted(n for n, e in _manifest()["skills"].items() if e.get("chars"))
    if MANIFEST.exists() else [],
)
def test_every_file_a_body_names_was_captured(name: str) -> None:
    """The body opens with the base-directory line exactly when files were
    extracted, and every path it names under that directory is one of them."""
    text = (SKILLS_DIR / f"{name}.md").read_text(encoding="utf-8")
    files = _with_files().get(name, {})
    opens = text.startswith("Base directory for this skill: <bundled-skills-dir>\n")
    assert opens == bool(files), (
        f"{name}: base-directory line {'present' if opens else 'absent'} but "
        f"{len(files)} extracted files recorded"
    )
    missing = _capture_skills()._unresolved_refs(text, files)
    assert not missing, f"{name} names {missing} under its base directory, not captured"


@pytest.mark.parametrize(
    "path",
    (sorted(SKILLS_DIR.glob("*.md")) if SKILLS_DIR.is_dir() else []) + BUNDLE_FILES,
)
def test_no_volatile_paths_survive(path: Path) -> None:
    text = path.read_bytes().decode("utf-8")
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


def test_normalize_keeps_what_follows_each_replaced_value(tmp_path, monkeypatch) -> None:
    """Staged rather than asserted against a capture that may not contain one.

    The values are those of a real 2.1.289 `plugin-authoring` capture: its
    extraction directory, and a config directory made inside the capturing
    session's scratchpad, which the body names with the child's session id.
    Every one sits under a temp root, so a rewrite by path shape would turn each
    into one bare placeholder and lose which file a line means.
    """
    module = _capture_skills()
    base = "/tmp/claude-0/bundled-skills/2.1.289/8c0c0e8a5cd992e177fe3bb5860247af/plugin-authoring"
    cfg = ("/root/.claude/tmp/claude-0/-root-claude-config-work/"
           "bba96906-cd9d-486f-8f22-e925749fcfff/scratchpad/cc-config-2.1.289")
    sid = "2572ede1-6d59-4c47-9a85-3dddb122ec12"
    cwd = "/tmp/capture-cwd-c80skwui"
    body = (
        f"Base directory for this skill: {base}\n\n"
        f"Write each mod in its own child folder of `{cfg}/dev-mods/{sid}`.\n"
        f"Shown in `{base}/examples/pane.tsx`; the long form is {base}/reference.md.\n"
        f"The working directory is {cwd}.\n"
    )
    log = tmp_path / "0001.json"
    log.write_text(json.dumps({"session": {"session_id": sid, "cwd": cwd}}))
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", cfg)
    text, changed = module._normalize(body, module._placeholders(body, [log]))
    assert changed
    assert text == (
        "Base directory for this skill: <bundled-skills-dir>\n\n"
        "Write each mod in its own child folder of `<config-dir>/dev-mods/<session-id>`.\n"
        "Shown in `<bundled-skills-dir>/examples/pane.tsx`; the long form is "
        "<bundled-skills-dir>/reference.md.\n"
        "The working directory is <cwd>.\n"
    )
    assert module._unresolved_refs(text, {"examples/pane.tsx": b"", "reference.md": b""}) == []
    assert module._unresolved_refs(text, {"reference.md": b""}) == ["examples/pane.tsx"]


def test_normalize_replaces_a_path_only_where_a_path_segment_ends() -> None:
    """The default config directory is a prefix of the global config file's
    name; a session id names a transcript file by itself."""
    module = _capture_skills()
    sid = "2572ede1-6d59-4c47-9a85-3dddb122ec12"
    text, _ = module._normalize(
        "/root/.claude/settings.json, /root/.claude.json, /root/.claude-x and "
        f"/root/.claude. Transcript: {sid}.jsonl",
        {"/root/.claude": "<config-dir>", sid: "<session-id>"},
    )
    assert text == (
        "<config-dir>/settings.json, /root/.claude.json, /root/.claude-x and "
        "<config-dir>. Transcript: <session-id>.jsonl"
    )
