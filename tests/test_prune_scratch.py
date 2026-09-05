"""Regression tests for scripts/prune-scratch.sh.

The deletion logic needed four review rounds to close (a --session glob
hole that deleted the wrong non-empty session, then a symlinked-project
escape assert_under_root's string-prefix check could not see, then a
set -e abort with no summary, then a symlinked-root scan blind spot) and
had zero automated coverage while that happened -- everything above was
found and fixed by hand, against real synthetic trees, one round at a
time. These tests exist so a future change to this script gets the same
guarantees the drift check has always had from test_env_context.py: red
before merge, not red in someone's home directory after.

Every tree here is built under tmp_path and named to the script only via
CLAUDE_CODE_TMPDIR -- never a real root. The child environment is built
from scratch (PATH plus CLAUDE_CODE_TMPDIR only), following
test_claude_sh.py's _run rather than os.environ.copy(), so an ambient
CLAUDE_CODE_TMPDIR or a PATH carrying an unexpected `find` cannot mask a
regression by leaking into the child.
"""

import os
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "prune-scratch.sh"
UID = os.getuid()


def _run(tmp_root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    """Run prune-scratch.sh under a from-scratch environment.

    PATH is the real /usr/bin:/bin, not a stand-in: unlike
    test_claude_sh.py's fake `claude`, this script's own logic is what is
    under test, so it must run against real find/rmdir/du/ls/rm, not a
    mock of them. CLAUDE_CODE_TMPDIR is the only thing that tells the
    script where to look; no other variable is set, so nothing ambient in
    this test runner's own environment can substitute for it.
    """
    return subprocess.run(
        ["/bin/bash", str(SCRIPT), *args],
        env={"PATH": "/usr/bin:/bin", "CLAUDE_CODE_TMPDIR": str(tmp_root)},
        text=True,
        capture_output=True,
    )


def _claude_root(tmp_path: Path) -> Path:
    """The claude-<uid> directory the script computes from CLAUDE_CODE_TMPDIR=tmp_path."""
    root = tmp_path / f"claude-{UID}"
    root.mkdir()
    return root


def _scratchpad(root: Path, project: str, session: str) -> Path:
    pad = root / project / session / "scratchpad"
    pad.mkdir(parents=True)
    return pad


def test_tmpdir_honoured_when_claude_code_tmpdir_is_unset(tmp_path: Path) -> None:
    """The bug this closes: scratchpad.py's tmp_root() falls back to
    tempfile.gettempdir(), which checks $TMPDIR before defaulting to /tmp,
    but this script's root used to be a bare
    `${CLAUDE_CODE_TMPDIR:-/tmp}/claude-$(id -u)` shell expansion, which
    does not consult $TMPDIR at all. With CLAUDE_CODE_TMPDIR unset and
    TMPDIR pointed elsewhere, the hook named a scratchpad under $TMPDIR
    while this script silently scanned /tmp instead -- not even failing
    loudly, but reporting a clean "nothing to do" (or, worse, real counts
    from an unrelated /tmp/claude-0 left over from other activity) over a
    tree it never looked at. The root must resolve under $TMPDIR the same
    way the hook does whenever CLAUDE_CODE_TMPDIR is unset.
    """
    root = _claude_root(tmp_path)
    _scratchpad(root, "-proj", "session-empty")
    full = _scratchpad(root, "-proj", "session-full")
    (full / "keep.txt").write_text("work in progress\n")

    result = subprocess.run(
        ["/bin/bash", str(SCRIPT)],
        env={"PATH": "/usr/bin:/bin", "TMPDIR": str(tmp_path)},
        text=True,
        capture_output=True,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert f"scratch root: {root}" in result.stdout
    assert "prunable (empty): 1" in result.stdout
    assert "keep (non-empty): 1" in result.stdout


def test_session_glob_is_rejected_not_matched(tmp_path: Path) -> None:
    """The closed hole: --session 'session-*' must never reach the filesystem.

    Before the fix, find -name treated this as a glob and -print -quit
    picked whichever match it visited first -- here that would have been
    the non-empty session holding data, not the empty one a user might
    expect. The fix rejects any glob metacharacter at validation, before
    any project directory is even listed.
    """
    root = _claude_root(tmp_path)
    _scratchpad(root, "-proj", "session-aaa")
    full = _scratchpad(root, "-proj", "session-bbb")
    (full / "notes.md").write_text("real work\n")

    result = _run(tmp_path, "--session", "session-*", "--apply")

    assert result.returncode == 2, result.stdout + result.stderr
    assert "must not contain '*'" in result.stderr
    assert (full / "notes.md").read_text() == "real work\n"
    assert (root / "-proj" / "session-aaa").is_dir()


def test_ambiguous_session_id_across_projects_refuses(tmp_path: Path) -> None:
    """The same session id under two project slugs must refuse, not pick one."""
    root = _claude_root(tmp_path)
    _scratchpad(root, "-proj-one", "session-xyz")
    full = _scratchpad(root, "-proj-two", "session-xyz")
    (full / "f.txt").write_text("data\n")

    result = _run(tmp_path, "--session", "session-xyz", "--apply")

    assert result.returncode == 1, result.stdout + result.stderr
    assert "is ambiguous" in result.stderr
    assert str(root / "-proj-one" / "session-xyz") in result.stderr
    assert str(root / "-proj-two" / "session-xyz") in result.stderr
    assert (root / "-proj-one" / "session-xyz").is_dir()
    assert (full / "f.txt").read_text() == "data\n"


def test_symlinked_session_directory_is_refused(tmp_path: Path) -> None:
    """A symlink sitting at a session's position must be refused by name.

    Not unlinked: rm -rf on a symlink argument only ever removes the link
    itself, which is what an earlier version of this script did instead
    of refusing -- correct outcome, wrong tool for the job of a script
    whose purpose is deletion. It should say what it found.
    """
    root = _claude_root(tmp_path)
    victim = tmp_path / "victim"
    victim.mkdir()
    (victim / "precious.txt").write_text("precious\n")
    (root / "-proj").mkdir()
    (root / "-proj" / "symlinked-session").symlink_to(victim)

    result = _run(tmp_path, "--session", "symlinked-session", "--apply")

    assert result.returncode == 1, result.stdout + result.stderr
    assert "the session directory is a symlink" in result.stderr
    assert (root / "-proj" / "symlinked-session").is_symlink()
    assert (victim / "precious.txt").read_text() == "precious\n"


def test_symlinked_project_directory_is_refused(tmp_path: Path) -> None:
    """A symlink at a *project* position must not let --session escape the root.

    This is the second escape found: assert_under_root's original
    string-prefix check could not see a symlinked project, "$root"/*/
    happily enumerated it, and --session --apply deleted through it into
    an unrelated directory. The project loop now excludes a symlinked
    project outright, and reports it by name rather than falling through
    to a generic "not found".
    """
    root = _claude_root(tmp_path)
    victim = tmp_path / "victim"
    (victim / "escaped-session" / "scratchpad").mkdir(parents=True)
    (victim / "escaped-session" / "scratchpad" / "precious.txt").write_text("precious\n")
    (root / "-projLink").symlink_to(victim)

    result = _run(tmp_path, "--session", "escaped-session", "--apply")

    assert result.returncode == 1, result.stdout + result.stderr
    assert "its project directory is a symlink" in result.stderr
    assert (victim / "escaped-session" / "scratchpad" / "precious.txt").read_text() == "precious\n"


def test_symlinked_root_is_scanned(tmp_path: Path) -> None:
    """A deliberately relocated root (CLAUDE_CODE_TMPDIR through a symlink)
    must be scanned as if real, not report 0/0 for a tree that plainly
    exists.

    find -H follows the root argument itself while still refusing
    to follow anything found while descending, so this and the symlinked
    escape tests above both hold at once.
    """
    base = tmp_path / "base"
    base.mkdir()
    victim = tmp_path / "victim"
    _scratchpad(victim, "-someproj", "session-a")
    full = _scratchpad(victim, "-someproj", "session-b")
    (full / "notes.txt").write_text("data\n")
    (base / f"claude-{UID}").symlink_to(victim)

    dry = _run(base)
    assert dry.returncode == 0, dry.stdout + dry.stderr
    assert "prunable (empty): 1" in dry.stdout
    assert "keep (non-empty): 1" in dry.stdout

    applied = _run(base, "--apply")
    assert applied.returncode == 0, applied.stdout + applied.stderr
    assert not (victim / "-someproj" / "session-a").exists()
    assert (full / "notes.txt").read_text() == "data\n"


def test_bulk_apply_deletes_only_empty_scratchpads(tmp_path: Path) -> None:
    root = _claude_root(tmp_path)
    _scratchpad(root, "-proj", "session-empty")
    full = _scratchpad(root, "-proj", "session-full")
    (full / "keep.txt").write_text("work in progress\n")

    result = _run(tmp_path, "--apply")

    assert result.returncode == 0, result.stdout + result.stderr
    assert not (root / "-proj" / "session-empty").exists()
    assert (full / "keep.txt").read_text() == "work in progress\n"


def test_bulk_apply_removes_now_empty_parent_session_directory(tmp_path: Path) -> None:
    """Deleting the scratchpad also removes the session dir it was the only child of.

    The header states this is intended, not a side effect: a session
    directory with nothing left in it once its (only) scratchpad is gone
    should not linger as an empty husk.
    """
    root = _claude_root(tmp_path)
    pad = _scratchpad(root, "-proj", "session-empty")
    session_dir = pad.parent

    result = _run(tmp_path, "--apply")

    assert result.returncode == 0, result.stdout + result.stderr
    assert not session_dir.exists()


def test_session_with_no_scratchpad_reported_but_not_bulk_deleted(tmp_path: Path) -> None:
    """A session holding only e.g. tasks/ (no scratchpad at all) must not
    be invisible to the report, and must survive bulk --apply.

    Only a
    --session <id> --apply naming it removes it. Measured on the real
    root during review: a session with 24K under tasks/ and no
    scratchpad appeared in neither count under the old scratchpad-depth
    scan, while --session --apply would still have deleted it whole.
    """
    root = _claude_root(tmp_path)
    tasks_only = root / "-proj" / "session-tasks-only"
    (tasks_only / "tasks").mkdir(parents=True)
    (tasks_only / "tasks" / "x.output").write_text("output\n")

    report = _run(tmp_path)
    assert report.returncode == 0, report.stdout + report.stderr
    assert "no scratchpad: 1" in report.stdout
    assert str(tasks_only) in report.stdout

    applied = _run(tmp_path, "--apply")
    assert applied.returncode == 0, applied.stdout + applied.stderr
    assert tasks_only.is_dir()
    assert (tasks_only / "tasks" / "x.output").read_text() == "output\n"

    named = _run(tmp_path, "--session", "session-tasks-only", "--apply")
    assert named.returncode == 0, named.stdout + named.stderr
    assert not tasks_only.exists()


def test_rmdir_refusal_is_skipped_not_fatal(tmp_path: Path) -> None:
    """A scratchpad misread as empty must be skipped, not fatal.

    ls -A's output is read through $(...), which strips trailing newlines,
    so a scratchpad whose only entry is a file named entirely of newline
    bytes is misread as empty. rmdir then correctly refuses to remove it;
    without tolerating that refusal, set -e used to abort the whole loop
    with no summary after whatever had already been deleted. The loop
    must instead skip it, count it, and keep going.
    """
    root = _claude_root(tmp_path)
    _scratchpad(root, "-proj", "session-normal-empty")
    nlfile_pad = _scratchpad(root, "-proj", "session-nlfile")
    (nlfile_pad / "\n").write_text("")

    result = _run(tmp_path, "--apply")

    assert result.returncode == 0, result.stdout + result.stderr
    assert "not actually empty (rmdir refused)" in result.stderr
    assert "deleted 1 empty scratchpads" in result.stdout
    assert "skipped 1 (not actually empty)" in result.stdout
    assert not (root / "-proj" / "session-normal-empty").exists()
    assert (nlfile_pad / "\n").exists()


def test_unknown_top_level_argument_exits_2(tmp_path: Path) -> None:
    result = _run(tmp_path, "--bogus-flag")
    assert result.returncode == 2, result.stdout + result.stderr
    assert "unknown argument" in result.stderr


@pytest.mark.parametrize(
    ("session_id", "expected_message"),
    [
        ("", "--session needs an id"),
        (".", "must not be empty, '.', or '..'"),
        ("..", "must not be empty, '.', or '..'"),
        ("a/b", "must not contain '/'"),
        ("a\\b", "must not contain a backslash"),
        ("a*b", "must not contain '*'"),
        ("a?b", "must not contain '?'"),
        ("a[b", "must not contain '['"),
    ],
)
def test_bad_session_id_exits_2(
    tmp_path: Path, session_id: str, expected_message: str
) -> None:
    args = ("--session", session_id) if session_id else ("--session",)
    result = _run(tmp_path, *args)
    assert result.returncode == 2, result.stdout + result.stderr
    assert expected_message in result.stderr
