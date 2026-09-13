"""Tests for the env-context SessionStart hook."""

import importlib
import io
import json
import os
import re
import stat
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import cast

import pytest

from claude_config.env_context import drift, environment, render, scratchpad


def test_package_imports() -> None:
    module = importlib.import_module("claude_config.env_context")
    assert module.__file__ is not None
    assert module.__file__.endswith("__init__.py")


def _fake_tree(root: Path, shells: list[str]) -> None:
    """Create executable stubs at the given absolute-looking paths under root."""
    for rel in shells:
        target = root / rel.lstrip("/")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("#!/bin/sh\n")
        target.chmod(0o755)


def _init_repo(path: Path) -> None:
    """Create a minimal real git repo at path, with one commit on HEAD."""
    path.mkdir(parents=True, exist_ok=True)

    def run(*args: str) -> None:
        subprocess.run(args, cwd=path, check=True, capture_output=True, text=True)

    run("git", "init", "-q")
    run("git", "config", "user.email", "test@example.com")
    run("git", "config", "user.name", "Test")
    run("git", "-c", "commit.gpgsign=false", "commit", "-q", "--allow-empty", "-m", "init")


def test_shell_override_wins(tmp_path: Path) -> None:
    _fake_tree(tmp_path, ["/opt/custom/bash", "/bin/zsh"])
    result = environment.resolve_shell(
        env={"CLAUDE_CODE_SHELL": str(tmp_path / "opt/custom/bash")},
        search_dirs=[str(tmp_path / "bin")],
        found=lambda _: None,
    )
    assert result == str(tmp_path / "opt/custom/bash")


def test_shell_override_ignored_when_not_bash_or_zsh(tmp_path: Path) -> None:
    # resolve_shell decides this with a substring test over the whole fake
    # path, tmp_path included. pytest derives tmp_path from this test's name
    # truncated to 30 chars; if a rename ever made that truncated name
    # contain "bash" or "zsh", the assertion below would pass or fail for the
    # wrong reason. Guard it so a rename fails loudly instead of silently
    # inverting the test.
    assert "bash" not in str(tmp_path) and "zsh" not in str(tmp_path)
    _fake_tree(tmp_path, ["/opt/custom/fish", "/bin/zsh"])
    result = environment.resolve_shell(
        env={"CLAUDE_CODE_SHELL": str(tmp_path / "opt/custom/fish")},
        search_dirs=[str(tmp_path / "bin")],
        found=lambda _: None,
    )
    assert result == str(tmp_path / "bin/zsh")


def test_zsh_preferred_when_shell_unset(tmp_path: Path) -> None:
    _fake_tree(tmp_path, ["/bin/bash", "/bin/zsh"])
    result = environment.resolve_shell(
        env={},
        search_dirs=[str(tmp_path / "bin")],
        found=lambda _: None,
    )
    assert result == str(tmp_path / "bin/zsh")


def test_bash_preferred_when_shell_names_bash(tmp_path: Path) -> None:
    _fake_tree(tmp_path, ["/bin/bash", "/bin/zsh"])
    result = environment.resolve_shell(
        # Names bash, so it drives the ordering, but does not exist — a real
        # path here would be prepended as a valid $SHELL and win outright,
        # returning the machine's own bash instead of the fixture's.
        env={"SHELL": "/nonexistent/bash"},
        search_dirs=[str(tmp_path / "bin")],
        found=lambda _: None,
    )
    assert result == str(tmp_path / "bin/bash")


def test_falls_back_to_bash_when_no_zsh(tmp_path: Path) -> None:
    _fake_tree(tmp_path, ["/bin/bash"])
    result = environment.resolve_shell(
        env={},
        search_dirs=[str(tmp_path / "bin")],
        found=lambda _: None,
    )
    assert result == str(tmp_path / "bin/bash")


def test_raises_when_no_shell_exists(tmp_path: Path) -> None:
    (tmp_path / "bin").mkdir()
    try:
        environment.resolve_shell(
            env={}, search_dirs=[str(tmp_path / "bin")], found=lambda _: None
        )
    except RuntimeError as exc:
        assert "no bash or zsh" in str(exc).lower()
    else:
        raise AssertionError("expected RuntimeError")


def test_is_git_repo_true_in_repo(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    _init_repo(repo)
    assert environment.is_git_repo(str(repo)) is True


def test_is_git_repo_false_outside_repo(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # git rev-parse walks upward looking for a repo; without a ceiling this
    # would flip to True if the pytest basetemp root ever sat inside one.
    monkeypatch.setenv("GIT_CEILING_DIRECTORIES", str(tmp_path))
    outside = tmp_path / "not-a-repo"
    outside.mkdir()
    assert environment.is_git_repo(str(outside)) is False


def test_is_git_repo_false_for_nonexistent_cwd(tmp_path: Path) -> None:
    missing = tmp_path / "does-not-exist"
    assert environment.is_git_repo(str(missing)) is False


def test_is_git_repo_false_when_cwd_is_a_file(tmp_path: Path) -> None:
    not_a_dir = tmp_path / "file"
    not_a_dir.write_text("")
    assert environment.is_git_repo(str(not_a_dir)) is False


def test_is_git_repo_false_when_git_missing_from_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("PATH", str(tmp_path))
    assert environment.is_git_repo(str(tmp_path)) is False


def test_worktree_common_dir_none_outside_repo(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Same upward-walk hazard as test_is_git_repo_false_outside_repo above.
    monkeypatch.setenv("GIT_CEILING_DIRECTORIES", str(tmp_path))
    outside = tmp_path / "not-a-repo"
    outside.mkdir()
    assert environment.worktree_common_dir(str(outside)) is None


def test_worktree_common_dir_none_for_plain_checkout(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    _init_repo(repo)
    assert environment.worktree_common_dir(str(repo)) is None


def test_worktree_common_dir_none_for_nonexistent_cwd(tmp_path: Path) -> None:
    missing = tmp_path / "does-not-exist"
    assert environment.worktree_common_dir(str(missing)) is None


def test_worktree_common_dir_none_when_cwd_is_a_file(tmp_path: Path) -> None:
    not_a_dir = tmp_path / "file"
    not_a_dir.write_text("")
    assert environment.worktree_common_dir(str(not_a_dir)) is None


def test_worktree_common_dir_none_when_git_missing_from_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("PATH", str(tmp_path))
    assert environment.worktree_common_dir(str(tmp_path)) is None


def test_worktree_common_dir_returns_shared_dir_for_linked_worktree(tmp_path: Path) -> None:
    main = tmp_path / "main"
    _init_repo(main)
    worktree = tmp_path / "linked"
    subprocess.run(
        ["git", "worktree", "add", "-q", "-b", "linked-branch", str(worktree)],
        cwd=main,
        check=True,
        capture_output=True,
        text=True,
    )
    result = environment.worktree_common_dir(str(worktree))
    assert result is not None
    assert Path(result).resolve() == (main / ".git").resolve()


def test_git_timeout_is_2_seconds(monkeypatch: pytest.MonkeyPatch) -> None:
    """Pins the per-call timeout directly, mirroring how
    test_installed_version_raises_on_timeout pins drift.installed_version's.
    _git() is called twice per hook run (is_git_repo, worktree_common_dir),
    so this number is half of what a hung git costs the whole hook -- see
    the design spec's "Timeout budget" section for the arithmetic across
    all three related numbers this shares a budget with.
    """

    def fake_run(*args: object, **kwargs: object) -> subprocess.CompletedProcess[str]:
        assert kwargs["timeout"] == 2
        raise subprocess.TimeoutExpired(cmd=["git"], timeout=2)

    monkeypatch.setattr(subprocess, "run", fake_run)
    assert environment.is_git_repo("/tmp") is False


def test_os_version_returns_nonempty_string() -> None:
    result = environment.os_version()
    assert isinstance(result, str)
    assert result != ""


def test_platform_name_returns_nonempty_string() -> None:
    result = environment.platform_name()
    assert isinstance(result, str)
    assert result != ""


def test_tmp_root_prefers_env(tmp_path: Path) -> None:
    assert scratchpad.tmp_root({"CLAUDE_CODE_TMPDIR": str(tmp_path)}) == str(tmp_path)


def test_tmp_root_empty_string_falls_through() -> None:
    # cc's Spe() is `K.CLAUDE_CODE_TMPDIR || os.tmpdir()`; JS `||` treats ""
    # as falsy exactly like Python's `or`, so an empty override must fall
    # through to the same place an unset one does.
    assert scratchpad.tmp_root({"CLAUDE_CODE_TMPDIR": ""}) == scratchpad.tmp_root({})


def test_tmp_root_fallback_is_an_existing_directory() -> None:
    # Deliberately not `== tempfile.gettempdir()`: that would only restate
    # tmp_root's own implementation and could never fail. Node's
    # os.tmpdir() reads TMPDIR || TMP || TEMP; Python's
    # tempfile.gettempdir() reads TMPDIR, TEMP, TMP -- a reordering that
    # disagrees with cc whenever TMP and TEMP are both set to different
    # real paths. Task 9's CLAUDE_CODE_TMPDIR export is what actually keeps
    # this module and cc in agreement in a real session, short-circuiting
    # that ordering difference; this only guards that whatever fallback
    # this module picks is at least a real, usable directory.
    assert Path(scratchpad.tmp_root({})).is_dir()


def test_slug_replaces_non_alphanumerics() -> None:
    assert scratchpad.project_slug("/root/claude-config-work") == "-root-claude-config-work"


def test_slug_raises_past_the_cc_limit() -> None:
    long_cwd = "/" + ("a" * 250)
    try:
        scratchpad.project_slug(long_cwd)
    except ValueError as exc:
        assert "200" in str(exc)
    else:
        raise AssertionError("expected ValueError")


def test_path_matches_cc_layout(tmp_path: Path) -> None:
    path = scratchpad.scratchpad_path(
        env={"CLAUDE_CODE_TMPDIR": str(tmp_path)},
        cwd="/root/claude-config-work",
        session_id="abc-123",
        uid=0,
    )
    assert path == tmp_path / "claude-0" / "-root-claude-config-work" / "abc-123" / "scratchpad"


def test_ensure_creates_private_directory(tmp_path: Path) -> None:
    path = scratchpad.ensure(
        env={"CLAUDE_CODE_TMPDIR": str(tmp_path)},
        cwd="/root/claude-config-work",
        session_id="abc-123",
        uid=0,
    )
    assert path.is_dir()
    assert stat.S_IMODE(path.stat().st_mode) == 0o700
    again = scratchpad.ensure(
        env={"CLAUDE_CODE_TMPDIR": str(tmp_path)},
        cwd="/root/claude-config-work",
        session_id="abc-123",
        uid=0,
    )
    assert again == path


def test_scratchpad_path_requires_session_id() -> None:
    # session_id has no default -- unlike env/cwd/uid, whose None each
    # stand for a real fallback (the real environment, the real cwd, the
    # real uid), "" would stand for nothing; there is no "current session
    # id" to fall back to. A missing one used to vanish silently instead of
    # raising, because Path("x") / "" is a no-op.
    with pytest.raises(TypeError):
        scratchpad.scratchpad_path(  # pyright: ignore[reportCallIssue]
            env={}, cwd="/root/claude-config-work", uid=0
        )


def test_ensure_requires_session_id() -> None:
    with pytest.raises(TypeError):
        scratchpad.ensure(  # pyright: ignore[reportCallIssue]
            env={}, cwd="/root/claude-config-work", uid=0
        )


def test_ensure_does_not_restrict_the_tmp_root(tmp_path: Path) -> None:
    # Not a regression guard for the old positional-.parent bug: this
    # passes against 4e92671 too, since a real session_id already made
    # that code identify uid_dir correctly there. What it actually
    # asserts: mkdir's `mode` only applies to the leaf of a given call, so
    # when parents=True has to create a missing tmp root on the way to
    # uid_dir, that tmp root comes out at whatever default permissions an
    # ordinary mkdir gives it in this process's umask -- not the
    # restrictive 0700 ensure() reserves for uid_dir and the scratchpad leaf.
    tmp_root = tmp_path / "does-not-exist-yet"
    control = tmp_path / "control"
    control.mkdir()
    scratchpad.ensure(
        env={"CLAUDE_CODE_TMPDIR": str(tmp_root)},
        cwd="/root/claude-config-work",
        session_id="abc-123",
        uid=0,
    )
    assert tmp_root.is_dir()
    assert stat.S_IMODE(tmp_root.stat().st_mode) == stat.S_IMODE(control.stat().st_mode)


def test_slug_at_200_chars_returns_unhashed() -> None:
    # Exact boundary: cc's q9() is `if (t.length <= vie) return t`, so 200
    # itself must still pass through unhashed. Only testing the 251-char
    # case (as test_slug_raises_past_the_cc_limit does) leaves `>` free to
    # mutate to `>=` without failing the suite.
    cwd = "a" * 200
    assert scratchpad.project_slug(cwd) == cwd


def test_slug_at_201_chars_raises() -> None:
    cwd = "a" * 201
    with pytest.raises(ValueError):
        scratchpad.project_slug(cwd)


def test_slug_rejects_empty_cwd() -> None:
    # Same bug _validate_session_id closes for session ids: an empty slug
    # would drop its own path segment, since Path('/a') / '' is a no-op.
    # Not reachable from cc, which always sends a real cwd, but consistency
    # matters more than reachability here.
    with pytest.raises(ValueError):
        scratchpad.project_slug("")


def test_scratchpad_path_and_ensure_agree_under_symlinked_tmp_root(tmp_path: Path) -> None:
    # The module's founding bug, reintroduced inside the module: ensure()
    # realpathed claude-<uid> (matching cc's yJ()) but scratchpad_path()
    # did not, so the two could name different directories for the same
    # input whenever the tmp root is itself a symlink -- as TMPDIR is on
    # macOS, under /var -> /private/var. Latent on this host only because
    # /tmp here is not a symlink.
    #
    # `path == created` alone cannot catch a regression here: ensure() now
    # returns scratchpad_path()'s value verbatim, so that equality holds
    # whether or not realpath runs at all. The absolute assertion below is
    # what actually exercises the realpath call -- confirmed by deleting
    # os.path.realpath from scratchpad_path and watching it fail.
    real_root = tmp_path / "real_tmp"
    real_root.mkdir()
    link_root = tmp_path / "link_tmp"
    link_root.symlink_to(real_root)
    env = {"CLAUDE_CODE_TMPDIR": str(link_root)}

    path = scratchpad.scratchpad_path(
        env=env, cwd="/root/claude-config-work", session_id="abc-123", uid=0
    )
    created = scratchpad.ensure(
        env=env, cwd="/root/claude-config-work", session_id="abc-123", uid=0
    )
    assert path == created
    assert (
        created
        == real_root / "claude-0" / "-root-claude-config-work" / "abc-123" / "scratchpad"
    )


def test_scratchpad_path_and_ensure_agree_when_uid_dir_itself_is_a_symlink(
    tmp_path: Path,
) -> None:
    # A second, distinct shape of the same bug: claude-<uid> itself (not
    # just an ancestor of the tmp root) can be a symlink. Same caveat as
    # above: `path == created` cannot fail on its own, so this also
    # asserts the absolute path -- here with no claude-0 component at all,
    # since realpath resolves the whole symlink away.
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    (tmp_path / "claude-0").symlink_to(elsewhere)
    env = {"CLAUDE_CODE_TMPDIR": str(tmp_path)}

    path = scratchpad.scratchpad_path(
        env=env, cwd="/root/claude-config-work", session_id="abc-123", uid=0
    )
    created = scratchpad.ensure(
        env=env, cwd="/root/claude-config-work", session_id="abc-123", uid=0
    )
    assert path == created
    assert created == elsewhere / "-root-claude-config-work" / "abc-123" / "scratchpad"


@pytest.mark.parametrize(
    "bad_session_id", ["", ".", "..", "/etc", "../../escape", "a/b", "a\\b"]
)
def test_scratchpad_path_rejects_unsafe_session_id(bad_session_id: str) -> None:
    with pytest.raises(ValueError):
        scratchpad.scratchpad_path(cwd="/root/claude-config-work", session_id=bad_session_id)


def test_ensure_rejects_unsafe_session_id_without_mutating(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        scratchpad.ensure(
            env={"CLAUDE_CODE_TMPDIR": str(tmp_path)},
            cwd="/root/claude-config-work",
            session_id="../../escape",
            uid=0,
        )
    assert list(tmp_path.iterdir()) == []


def test_ensure_rejects_oversized_slug_without_mutating(tmp_path: Path) -> None:
    # Regression guard: uid_dir.mkdir() used to run before project_slug(cwd)
    # could raise, so claude-0 existed on disk after a rejected cwd.
    long_cwd = "/" + ("a" * 250)
    with pytest.raises(ValueError):
        scratchpad.ensure(
            env={"CLAUDE_CODE_TMPDIR": str(tmp_path)},
            cwd=long_cwd,
            session_id="abc-123",
            uid=0,
        )
    assert list(tmp_path.iterdir()) == []


def test_ensure_repairs_a_preexisting_uid_dir_mode(tmp_path: Path) -> None:
    # Mirrors cc's JIt(): fchmodSync whenever the existing mode isn't
    # already 0700, not just a mode requested at creation time (which
    # mkdir(exist_ok=True) leaves alone for a directory that already
    # existed).
    uid_dir = tmp_path / "claude-0"
    uid_dir.mkdir(mode=0o755)
    assert stat.S_IMODE(uid_dir.stat().st_mode) == 0o755

    scratchpad.ensure(
        env={"CLAUDE_CODE_TMPDIR": str(tmp_path)},
        cwd="/root/claude-config-work",
        session_id="abc-123",
        uid=0,
    )
    assert stat.S_IMODE(uid_dir.stat().st_mode) == 0o700


def _facts(**overrides: object) -> render.Facts:
    # Built as a plain dict and cast at the end, rather than typed as
    # render.Facts throughout: **overrides is deliberately untyped (object),
    # so TypedDict.update() would fight the checker at every call site for a
    # helper whose whole point is ad hoc per-test overrides.
    base: dict[str, object] = {
        "cwd": "/root/claude-config-work",
        "is_git_repo": True,
        "worktree_common_dir": None,
        "platform": "linux",
        "shell": "/bin/bash",
        "os_version": "Linux 6.18.7",
        "model": "claude-opus-5",
        "session_id": "abc-123",
        "scratchpad": "/root/.claude/tmp/claude-0/-root-claude-config-work/abc-123/scratchpad",
        "drift_note": None,
    }
    base.update(overrides)
    # dict[str, object] and Facts don't structurally overlap enough for a
    # direct cast (Facts pins is_git_repo to bool, not object) -- go through
    # object, the standard escape hatch for an intentionally-unchecked cast.
    return cast(render.Facts, cast(object, base))


def test_env_block_has_expected_bullets() -> None:
    text = render.sections(_facts())
    assert text.startswith("# Environment\nYou have been invoked in the following environment: \n")
    assert " - Primary working directory: /root/claude-config-work" in text
    assert " - Is a git repository: true" in text
    assert " - Platform: linux" in text
    assert " - Shell: /bin/bash" in text
    assert " - OS Version: Linux 6.18.7" in text
    assert " - You are powered by the model claude-opus-5" in text
    assert " - Session ID: abc-123" in text


def test_model_line_omitted_when_absent() -> None:
    text = render.sections(_facts(model=None))
    assert "powered by the model" not in text


def test_worktree_lines_present_only_in_a_worktree() -> None:
    plain = render.sections(_facts())
    assert "git worktree" not in plain

    linked = render.sections(_facts(worktree_common_dir="/repos/claude-config/.git"))
    # Not .../.git: the common-dir's trailing .git names the git directory,
    # not the checkout an agent should read or run commands in.
    assert " - This is a git worktree of /repos/claude-config." in linked
    assert "git stash" in linked


def test_worktree_line_names_bare_main_unchanged() -> None:
    """A bare main's common-dir has no `.git` path component to strip.

    `/repos/bare-repo.git` ends in the four characters ".git" but its last
    path *component* is "bare-repo.git", not ".git" -- unlike the linked-
    worktree case above, where the last component is exactly ".git". Only
    the latter should be stripped to its parent.
    """
    text = render.sections(_facts(worktree_common_dir="/repos/bare-repo.git"))
    assert " - This is a git worktree of /repos/bare-repo.git." in text


def test_scratchpad_section_names_the_path() -> None:
    text = render.sections(_facts())
    assert "# Scratchpad Directory" in text
    assert "/root/.claude/tmp/claude-0/-root-claude-config-work/abc-123/scratchpad" in text


def test_drift_note_appears_as_a_bullet() -> None:
    text = render.sections(_facts(drift_note="Claude Code 2.1.240 changed its env block."))
    assert " - NOTE: Claude Code 2.1.240 changed its env block." in text


def test_git_repo_false_renders_lowercase() -> None:
    text = render.sections(_facts(is_git_repo=False))
    assert " - Is a git repository: false" in text


def test_scratchpad_section_omitted_when_unavailable() -> None:
    """An uncreatable scratchpad must cost the section, not the whole block."""
    text = render.sections(_facts(scratchpad=None))
    assert "# Scratchpad Directory" not in text
    assert "None" not in text
    assert "# Environment" in text


def test_full_text_matches_snapshot_when_fully_populated() -> None:
    """Pins bullet order, the header's trailing space, the blank line between
    sections, and that every bullet after the header carries the ` - ` prefix
    -- properties none of the substring assertions above pin individually.
    """
    text = render.sections(
        _facts(drift_note="Claude Code 2.1.240 changed its env block.")
    )
    expected = '# Environment\nYou have been invoked in the following environment: \n - Primary working directory: /root/claude-config-work\n - Is a git repository: true\n - Platform: linux\n - Shell: /bin/bash\n - OS Version: Linux 6.18.7\n - You are powered by the model claude-opus-5\n - Session ID: abc-123\n - NOTE: Claude Code 2.1.240 changed its env block.\n\n# Scratchpad Directory\n\nUse this directory for temporary files instead of `/tmp` or other system temp directories:\n`/root/.claude/tmp/claude-0/-root-claude-config-work/abc-123/scratchpad`\n\nOnly use `/tmp` if the user explicitly requests it.\n\nIt is session-specific, isolated from the project, and is normally the same directory your subagents are given.'
    assert text == expected


def test_full_text_matches_snapshot_for_worktree() -> None:
    """Companion to the snapshot above: pins the worktree and stash-caution
    lines' exact wording and position in the bullet order.
    """
    text = render.sections(_facts(worktree_common_dir="/repos/claude-config/.git"))
    expected = '# Environment\nYou have been invoked in the following environment: \n - Primary working directory: /root/claude-config-work\n - This is a git worktree of /repos/claude-config. Run all commands from this directory and make changes only here; reading /repos/claude-config is fine, but do not edit, commit, or build there.\n - The git stash stack is shared with the main checkout and all other worktrees, and other Claude sessions may push or pop it concurrently. Never use bare `git stash` / `git stash pop` — you could pop another session\'s changes. Prefer a temporary WIP commit to set work aside; if you must stash, use `git stash push -u -m "<unique-tag>"`, immediately capture your entry\'s SHA via `git stash list --format=\'%H %gs\'`, restore with `git stash apply <sha>` (not pop), and afterwards drop the entry, re-finding its current `stash@{n}` by tag first.\n - Is a git repository: true\n - Platform: linux\n - Shell: /bin/bash\n - OS Version: Linux 6.18.7\n - You are powered by the model claude-opus-5\n - Session ID: abc-123\n\n# Scratchpad Directory\n\nUse this directory for temporary files instead of `/tmp` or other system temp directories:\n`/root/.claude/tmp/claude-0/-root-claude-config-work/abc-123/scratchpad`\n\nOnly use `/tmp` if the user explicitly requests it.\n\nIt is session-specific, isolated from the project, and is normally the same directory your subagents are given.'
    assert text == expected


def _binary(
    tmp_path: Path,
    literals: list[str],
    before: list[str] | None = None,
    far: list[str] | None = None,
) -> Path:
    """A stand-in binary: padding, optional pre-anchor literals, both
    anchors, post-anchor literals, then far strings.

    Both anchors, because production has two jobs for them and 2.1.269 split
    the strings that do them: `find_binary` identifies the binary by ANCHOR,
    while `literals_in` windows on WINDOW_ANCHOR. Writing only one would
    leave whichever test needs the other reading a binary cc would never
    produce.

    `before` mirrors production: roughly half the pinned window literals sit
    *before* the window anchor, so a fixture that places everything after it
    never exercises WINDOW_BEFORE at all. `far` lands well past the scan
    window, standing in for the whole-binary reuse `required_literals`
    counts rather than the window sees.

    Every literal is NUL-delimited on both sides and the padding is far
    wider than WINDOW_AFTER, so no match can touch a window edge -- which
    `literals_in` discards as a half-read string, and which would otherwise
    silently drop a fixture literal a test is asserting on.
    """
    blob = b"\x00" * 100
    for text in before or []:
        blob += text.encode() + b"\x00"
    blob += drift.ANCHOR + b"\x00" + drift.WINDOW_ANCHOR
    for text in literals:
        blob += b"\x00" + text.encode()
    blob += b"\x00" * 8000
    for text in far or []:
        blob += b"\x00" + text.encode()
    path = tmp_path / "claude.exe"
    path.write_bytes(blob)
    return path


def _manifest(tmp_path: Path, window: list[str], required: dict[str, int]) -> Path:
    """`_binary()` always writes both anchors, so a manifest that can ever
    truly match one must always list them too -- centralized here rather
    than repeated as a comment at each call site.
    """
    path = tmp_path / "manifest.json"
    path.write_text(
        json.dumps(
            {
                "version": "2.1.235",
                "window_literals": sorted(
                    {*window, drift.ANCHOR.decode(), drift.WINDOW_ANCHOR.decode()}
                ),
                "required_literals": required,
            }
        )
    )
    return path


def _stub(path: Path, *, anchor: bool) -> None:
    """An executable stub file, optionally containing the env-block anchor."""
    content = b"#!/bin/sh\n"
    if anchor:
        content += drift.ANCHOR
    path.write_bytes(content)
    path.chmod(0o755)


def test_extract_finds_literals(tmp_path: Path) -> None:
    binary = _binary(
        tmp_path,
        ["Is a git repository: "],
        before=["Primary working directory: "],
    )
    literals = drift.extract_literals(binary)
    assert "Primary working directory: " in literals
    assert "Is a git repository: " in literals


def test_extract_excludes_strings_under_the_length_floor(tmp_path: Path) -> None:
    """PRINTABLE's {12,} floor is load-bearing: the committed manifest's
    shortest window literal (`# Environment`, 13 characters) sits right at
    the boundary. The synthetic fixtures elsewhere pad with NUL, which
    never produces sub-floor printable noise to exclude, so nothing so far
    distinguished {12,} from a much weaker {1,}.
    """
    binary = _binary(
        tmp_path,
        ["Primary working directory: "],
        before=["short"],  # 5 characters: must not survive the floor
    )
    literals = drift.extract_literals(binary)
    assert "short" not in literals
    assert "Primary working directory: " in literals


def test_extract_literals_returns_them_sorted(tmp_path: Path) -> None:
    """Task 10's --update regenerates window_literals from this function's
    output; order is what keeps a manifest diff reviewable, so the return
    value must actually be sorted -- not merely a set that happens, on a
    given run, to contain the right members in the right order.
    """
    binary = _binary(
        tmp_path,
        ["Zebra field one: ", "Apple field two: ", "Middle field three: "],
    )
    literals = drift.extract_literals(binary)
    assert literals == sorted(literals)


def test_extract_raises_without_anchor(tmp_path: Path) -> None:
    path = tmp_path / "not-claude"
    path.write_bytes(b"nothing here")
    try:
        drift.extract_literals(path)
    except RuntimeError as exc:
        assert "anchor" in str(exc)
    else:
        raise AssertionError("expected RuntimeError")


def test_window_follows_the_field_anchor_not_the_binary_anchor() -> None:
    """The 2.1.269 regression, in miniature.

    Through 2.1.235 one string did both jobs, because the bundler happened
    to lay cc's env-block opening sentence down beside the field templates.
    In 2.1.269 they sit ~420 KB apart, and a window still measured from the
    sentence returned markdown-parser regexes and HTTP/2 error strings --
    a full set of literals, none of them an env field, which re-pins clean
    and can never again catch a field change. The distance here is token;
    what matters is that the window is measured from WINDOW_ANCHOR.
    """
    decoy = b"Iterator result interface is not an object."
    field = b"Is a git repository: "
    data = (
        b"\x00" * 50
        + drift.ANCHOR
        + b"\x00"
        + decoy
        + b"\x00" * 5000
        + drift.WINDOW_ANCHOR
        + b"\x00"
        + field
        + b"\x00" * 5000
    )

    literals = drift.literals_in(data, "fixture")

    assert field.decode() in literals
    assert decoy.decode() not in literals


def test_literals_cut_by_a_window_edge_are_discarded() -> None:
    """Half a string is still a string `compare()` can diff, which is the
    problem: it moves whenever anything near the boundary shifts, reporting
    drift for releases that never touched the env block. The real pin
    carried two of these before this was fixed -- `lastIngressUuidBySession`
    entered the manifest as `essUuidBySession`.

    Both edges, because they are separately reachable: WINDOW_BEFORE clamps
    at 0 for an anchor near the start of the file and WINDOW_AFTER never
    does, so a guard written for one end can pass while the other leaks.
    """
    anchor_at = drift.WINDOW_BEFORE + 500
    leading = b"L" * 400  # starts before the window, ends inside it
    trailing = b"T" * 400  # starts inside the window, ends past it
    inside = b"Is a git repository: "

    prefix = bytearray(b"\x00" * anchor_at)
    prefix[300:300 + len(leading)] = leading
    suffix = bytearray(b"\x00" * (drift.WINDOW_AFTER + 500))
    start = drift.WINDOW_AFTER - len(drift.WINDOW_ANCHOR) - 200
    suffix[start:start + len(trailing)] = trailing
    suffix[50:50 + len(inside)] = inside

    literals = drift.literals_in(bytes(prefix) + drift.WINDOW_ANCHOR + bytes(suffix), "x")

    assert inside.decode() in literals
    assert leading.decode() not in literals
    assert trailing.decode() not in literals
    assert not any(set(literal) <= {"L"} for literal in literals), literals
    assert not any(set(literal) <= {"T"} for literal in literals), literals


def test_compare_matches_pinned_manifest(tmp_path: Path) -> None:
    literals = ["Primary working directory: ", "Is a git repository: "]
    binary = _binary(tmp_path, literals, far=["Shell: PowerShell"])
    manifest = _manifest(tmp_path, literals, {"Shell: PowerShell": 1})
    result = drift.compare(binary, manifest, version="2.1.235")
    assert result.matches
    assert result.added == []
    assert result.removed == []
    assert result.count_changes == {}


def test_compare_reports_a_new_field(tmp_path: Path) -> None:
    binary = _binary(
        tmp_path,
        ["Primary working directory: ", "Current sandbox mode: "],
        far=["Shell: PowerShell"],
    )
    manifest = _manifest(
        tmp_path, ["Primary working directory: "], {"Shell: PowerShell": 1}
    )
    result = drift.compare(binary, manifest, version="2.1.240")
    assert not result.matches
    assert result.added == ["Current sandbox mode: "]
    assert result.installed_version == "2.1.240"


def test_compare_reports_a_count_drop_outside_the_window(tmp_path: Path) -> None:
    """A rename scoped to cc's env builders leaves the string present elsewhere."""
    literals = ["Primary working directory: "]
    binary = _binary(tmp_path, literals, far=["Shell: PowerShell"])
    manifest = _manifest(tmp_path, literals, {"Shell: PowerShell": 3})
    result = drift.compare(binary, manifest, version="2.1.235")
    assert not result.matches
    assert result.count_changes == {"Shell: PowerShell": (3, 1)}
    assert result.added == []


def test_compare_reports_a_version_mismatch_even_when_fields_match(
    tmp_path: Path,
) -> None:
    """The scan sees labels only (module docstring): a cc release that
    changes behaviour without changing any label text still needs to trip
    the check, so the pinned version participates in `matches` even when
    every literal and every count agrees.
    """
    literals = ["Primary working directory: "]
    binary = _binary(tmp_path, literals)
    manifest = _manifest(tmp_path, literals, {})
    result = drift.compare(binary, manifest, version="2.1.240")
    assert not result.matches
    assert result.added == []
    assert result.removed == []
    assert result.count_changes == {}
    assert result.installed_version == "2.1.240"
    assert result.pinned_version == "2.1.235"


def test_compare_reports_a_removed_field(tmp_path: Path) -> None:
    """cc dropping or renaming a field is this module's headline job, yet
    `result.removed` was asserted in exactly two places before this, both
    `== []` -- nothing positively exercised a real removal.
    """
    literals = ["Primary working directory: "]
    binary = _binary(tmp_path, literals)
    manifest = _manifest(tmp_path, [*literals, "Current sandbox mode: "], {})
    result = drift.compare(binary, manifest, version="2.1.235")
    assert not result.matches
    assert result.removed == ["Current sandbox mode: "]
    assert result.added == []


def test_compare_names_the_manifest_when_a_key_is_missing(tmp_path: Path) -> None:
    """A hand-edited manifest missing a required key must name the manifest
    file in the error -- the binary read already names its file via
    `literals_in`'s `source`; the manifest read had no equivalent.
    """
    literals = ["Primary working directory: "]
    binary = _binary(tmp_path, literals)
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps({"version": "2.1.235"}))  # no window_literals

    with pytest.raises(RuntimeError, match=re.escape(str(manifest))):
        drift.compare(binary, manifest, version="2.1.235")


def test_cache_avoids_a_second_scan(tmp_path: Path) -> None:
    literals = ["Primary working directory: "]
    binary = _binary(tmp_path, literals)
    manifest = _manifest(tmp_path, literals, {})
    cache = tmp_path / "cache.json"

    calls: list[int] = []

    def version() -> str:
        calls.append(1)
        return "2.1.235"

    first = drift.cached_note(binary, manifest, cache, version)
    second = drift.cached_note(binary, manifest, cache, version)
    assert first is None
    assert second is None
    assert len(calls) == 1


def test_cache_hit_returns_the_stored_note(tmp_path: Path) -> None:
    """Every hit-path test elsewhere has note is None, and every non-None
    assertion sits on a miss -- `return entry.get("note")` -> `return None`
    survived the whole suite. If that regressed, the module's headline
    output -- the drift warning itself -- would appear in exactly one
    session and then silently never again for the life of that
    binary/manifest pair.
    """
    literals = ["Primary working directory: "]
    binary = _binary(tmp_path, literals)
    manifest = _manifest(tmp_path, [*literals, "Current sandbox mode: "], {})
    cache = tmp_path / "cache.json"

    calls: list[int] = []

    def version() -> str:
        calls.append(1)
        return "2.1.235"

    first = drift.cached_note(binary, manifest, cache, version)
    assert first is not None  # a genuine drift note from the miss path

    second = drift.cached_note(binary, manifest, cache, version)
    assert len(calls) == 1  # confirms the second call was a real cache hit
    assert second == first


def test_cache_self_heals_from_a_corrupt_file(tmp_path: Path) -> None:
    """A torn write (or any unreadable cache) must be treated as a miss and
    overwritten, not raised -- otherwise every session after a corruption
    reports "drift check failed" forever, until a human deletes the file by
    hand.
    """
    literals = ["Primary working directory: "]
    binary = _binary(tmp_path, literals)
    manifest = _manifest(tmp_path, literals, {})
    cache = tmp_path / "cache.json"
    cache.write_text("{not valid json")

    note = drift.cached_note(binary, manifest, cache, lambda: "2.1.235")

    assert note is None
    assert json.loads(cache.read_text())["note"] is None


def test_cache_self_heals_from_wrong_shaped_json(tmp_path: Path) -> None:
    """Valid JSON that isn't an object -- a list, a string, a number -- is
    exactly as unusable as a parse failure, but `.get()` on it raises
    AttributeError instead of a caught parse error, escaping the earlier,
    narrower guard and wedging the cache just as permanently.
    """
    literals = ["Primary working directory: "]
    binary = _binary(tmp_path, literals)
    manifest = _manifest(tmp_path, literals, {})
    cache = tmp_path / "cache.json"
    cache.write_text("[]")

    note = drift.cached_note(binary, manifest, cache, lambda: "2.1.235")

    assert note is None
    assert json.loads(cache.read_text())["note"] is None


def test_cache_self_heals_from_invalid_utf8(tmp_path: Path) -> None:
    """Invalid UTF-8 raises UnicodeDecodeError from read_text() itself --
    a ValueError, like JSONDecodeError, but a different subclass, so a
    catch scoped to JSONDecodeError specifically lets it through.
    """
    literals = ["Primary working directory: "]
    binary = _binary(tmp_path, literals)
    manifest = _manifest(tmp_path, literals, {})
    cache = tmp_path / "cache.json"
    cache.write_bytes(b"\xff\xfe\x00not utf-8")

    note = drift.cached_note(binary, manifest, cache, lambda: "2.1.235")

    assert note is None
    assert json.loads(cache.read_text())["note"] is None


def test_cache_self_heals_from_an_oserror_on_read(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A read failure that is not a decode/parse problem at all -- the file
    vanishing between the is_file() check and the read, a real race in a
    globally shared cache -- must be caught too, not just ValueError. Only
    the existence check is faked here; the FileNotFoundError this raises on
    the actual, genuinely-absent path is real.
    """
    literals = ["Primary working directory: "]
    binary = _binary(tmp_path, literals)
    manifest = _manifest(tmp_path, literals, {})
    cache = tmp_path / "cache.json"  # deliberately never created

    monkeypatch.setattr(Path, "is_file", lambda self: True)

    note = drift.cached_note(binary, manifest, cache, lambda: "2.1.235")

    assert note is None


def test_cache_invalidates_when_binary_mtime_changes(tmp_path: Path) -> None:
    """A same-size touch must still force a rescan -- proving mtime_ns, not
    just size, participates in the cache key.
    """
    literals = ["Primary working directory: "]
    binary = _binary(tmp_path, literals)
    manifest = _manifest(tmp_path, literals, {})
    cache = tmp_path / "cache.json"

    calls: list[int] = []

    def version() -> str:
        calls.append(1)
        return "2.1.235"

    drift.cached_note(binary, manifest, cache, version)
    stat = binary.stat()
    new_ns = stat.st_mtime_ns + 1_000_000_000
    os.utime(binary, ns=(new_ns, new_ns))
    drift.cached_note(binary, manifest, cache, version)
    assert len(calls) == 2


def test_cache_invalidates_when_binary_size_changes(tmp_path: Path) -> None:
    """A size change pinned back to the original mtime must still force a
    rescan -- proving size, not just mtime_ns, participates in the cache key.
    """
    literals = ["Primary working directory: "]
    binary = _binary(tmp_path, literals)
    manifest = _manifest(tmp_path, literals, {})
    cache = tmp_path / "cache.json"

    calls: list[int] = []

    def version() -> str:
        calls.append(1)
        return "2.1.235"

    drift.cached_note(binary, manifest, cache, version)
    original_ns = binary.stat().st_mtime_ns
    with binary.open("ab") as fh:
        fh.write(b"\x00")
    os.utime(binary, ns=(original_ns, original_ns))
    drift.cached_note(binary, manifest, cache, version)
    assert len(calls) == 2


def test_cache_invalidates_when_manifest_is_repinned(tmp_path: Path) -> None:
    """`check-env-context.sh --update` re-pins the manifest in place; a
    stale drift note must not outlive the condition it described once the
    binary it was cached against is unchanged but the manifest now matches
    it. The manifest is keyed on content, not mtime, so this needs no
    timestamp manipulation: different content hashes differently, period.
    """
    literals = ["Primary working directory: ", "Current sandbox mode: "]
    binary = _binary(tmp_path, literals)
    cache = tmp_path / "cache.json"

    stale_manifest = _manifest(tmp_path, ["Primary working directory: "], {})
    stale_note = drift.cached_note(binary, stale_manifest, cache, lambda: "2.1.235")
    assert stale_note is not None

    updated_manifest = _manifest(tmp_path, literals, {})
    fresh_note = drift.cached_note(binary, updated_manifest, cache, lambda: "2.1.235")
    assert fresh_note is None


def test_cache_reuses_across_manifests_with_identical_content(
    tmp_path: Path,
) -> None:
    """Task 7 points every worktree at one global cache. This repo alone has
    five worktrees, each with its own manifest file and its own mtime; keying
    on mtime instead of content rescanned once per checkout even when the
    pinned manifests were byte-identical copies of each other. Keying on
    content means two such manifests share one cache entry.
    """
    literals = ["Primary working directory: "]
    binary = _binary(tmp_path, literals)
    cache = tmp_path / "cache.json"

    checkout_a = tmp_path / "checkout-a"
    checkout_a.mkdir()
    checkout_b = tmp_path / "checkout-b"
    checkout_b.mkdir()
    manifest_a = _manifest(checkout_a, literals, {})
    manifest_b = checkout_b / "manifest.json"
    manifest_b.write_bytes(manifest_a.read_bytes())

    calls: list[int] = []

    def version() -> str:
        calls.append(1)
        return "2.1.235"

    drift.cached_note(binary, manifest_a, cache, version)
    drift.cached_note(binary, manifest_b, cache, version)
    assert len(calls) == 1


def test_cache_distinguishes_binaries_by_path(tmp_path: Path) -> None:
    """Two different files -- as `find_binary()` could return across a Nix
    store upgrade -- must not share a cache entry merely because their size,
    mtime, and paired manifest happen to coincide.
    """
    literals = ["Primary working directory: "]
    binary_a = _binary(tmp_path, literals)
    binary_b = tmp_path / "claude-b.exe"
    binary_b.write_bytes(binary_a.read_bytes())
    stat_a = binary_a.stat()
    os.utime(binary_b, ns=(stat_a.st_mtime_ns, stat_a.st_mtime_ns))
    assert binary_a.stat().st_size == binary_b.stat().st_size

    manifest = _manifest(tmp_path, literals, {})
    cache = tmp_path / "cache.json"

    calls: list[int] = []

    def version() -> str:
        calls.append(1)
        return "2.1.235"

    drift.cached_note(binary_a, manifest, cache, version)
    drift.cached_note(binary_b, manifest, cache, version)
    assert len(calls) == 2


def test_cached_note_calls_installed_version_when_version_is_omitted(
    tmp_path: Path,
) -> None:
    """Every other cached_note test passes an explicit version callable.
    Task 7 calls `drift.cached_note(drift.find_binary(), MANIFEST, CACHE)`
    with no version at all -- the only branch production actually takes,
    and before this the only one with zero coverage: replacing
    `installed_version(binary)` with a literal in the source survived the
    whole suite.
    """
    literals = ["Primary working directory: "]
    header = b"#!/bin/sh\necho 9.9.9\nexit 0\n"
    blob = header + b"\x00" * 100
    blob += b"You have been invoked in the following environment: "
    for text_ in literals:
        blob += b"\x00" + text_.encode()
    blob += b"\x00" * 8000
    binary = tmp_path / "claude"
    binary.write_bytes(blob)
    binary.chmod(0o755)

    manifest = _manifest(tmp_path, literals, {})  # pins version "2.1.235"
    cache = tmp_path / "cache.json"

    note = drift.cached_note(binary, manifest, cache)

    assert note is not None
    assert "9.9.9" in note


def test_cache_write_failure_does_not_raise_and_still_returns_the_note(
    tmp_path: Path,
) -> None:
    """A cache that cannot be written -- here, a directory sitting at the
    cache path, standing in for a read-only filesystem or a full disk --
    must not turn a successful check into a raised exception. The note is
    still correct; only remembering it fails.
    """
    literals = ["Primary working directory: "]
    binary = _binary(tmp_path, literals)
    manifest = _manifest(tmp_path, [*literals, "Current sandbox mode: "], {})
    cache = tmp_path / "cache.json"
    cache.mkdir()  # a directory, not a file, at the cache path

    note = drift.cached_note(binary, manifest, cache, lambda: "2.1.235")

    assert note is not None
    assert "check-env-context.sh" in note


def test_cache_write_leaves_no_temp_file_behind(tmp_path: Path) -> None:
    """tmp-file-plus-replace must clean up after itself on the success
    path -- no stray .tmp sibling once the real cache file exists.
    """
    literals = ["Primary working directory: "]
    binary = _binary(tmp_path, literals)
    manifest = _manifest(tmp_path, literals, {})
    cache = tmp_path / "cache.json"

    drift.cached_note(binary, manifest, cache, lambda: "2.1.235")

    assert cache.is_file()
    strays = [
        p for p in tmp_path.iterdir() if p.name.startswith(cache.name) and p != cache
    ]
    assert strays == []


def test_cache_write_failure_preserves_the_existing_cache_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A failed write must not clobber a prior, still-valid cache -- the
    whole point of writing to a temp file first and renaming over the
    original only at the very end, rather than truncating it in place.
    """
    literals = ["Primary working directory: "]
    binary = _binary(tmp_path, literals)
    manifest = _manifest(tmp_path, literals, {})
    cache = tmp_path / "cache.json"
    cache.write_text('{"sentinel": true}')

    def fake_mkstemp(*args: object, **kwargs: object) -> tuple[int, str]:
        raise OSError("simulated: disk full")

    monkeypatch.setattr(tempfile, "mkstemp", fake_mkstemp)

    note = drift.cached_note(binary, manifest, cache, lambda: "2.1.235")

    assert note is None  # the check itself still succeeds
    assert cache.read_text() == '{"sentinel": true}'  # untouched by the failed write


def test_cache_creates_its_parent_directory_on_first_run(tmp_path: Path) -> None:
    """The line that makes a first run work: no test used a cache path
    whose parent was absent before this.
    """
    literals = ["Primary working directory: "]
    binary = _binary(tmp_path, literals)
    manifest = _manifest(tmp_path, literals, {})
    cache = tmp_path / "nested" / "does-not-exist-yet" / "cache.json"

    note = drift.cached_note(binary, manifest, cache, lambda: "2.1.235")

    assert note is None
    assert cache.is_file()


def test_cached_note_text_names_the_script(tmp_path: Path) -> None:
    binary = _binary(tmp_path, ["Current sandbox mode: "])
    manifest = _manifest(tmp_path, ["Old field: "], {})
    cache = tmp_path / "cache.json"
    note = drift.cached_note(binary, manifest, cache, lambda: "2.1.240")
    assert note is not None
    assert "2.1.240" in note
    assert "2.1.235" in note  # the pinned version, not just the installed one
    assert "check-env-context.sh" in note


def test_find_binary_uses_execpath_when_set(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    target = tmp_path / "claude.exe"
    _stub(target, anchor=True)
    monkeypatch.setenv("CLAUDE_CODE_EXECPATH", str(target))
    assert drift.find_binary() == Path(os.path.realpath(target))


def test_find_binary_resolves_execpath_through_a_symlink(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The EXECPATH branch must realpath its result too, like the other two
    branches -- otherwise one physical binary can key the cache under two
    different strings depending on which branch found it.
    """
    real = tmp_path / "claude.exe"
    _stub(real, anchor=True)
    link = tmp_path / "claude-link"
    link.symlink_to(real)
    monkeypatch.setenv("CLAUDE_CODE_EXECPATH", str(link))
    assert drift.find_binary() == real


def test_find_binary_follows_wrapped_sibling_when_path_claude_has_no_anchor(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("CLAUDE_CODE_EXECPATH", raising=False)
    bindir = tmp_path / "bin"
    bindir.mkdir()
    wrapper = bindir / "claude"
    _stub(wrapper, anchor=False)
    real = tmp_path / "claude.exe"
    _stub(real, anchor=True)
    (bindir / ".claude-wrapped").symlink_to(real)
    monkeypatch.setenv("PATH", str(bindir))
    assert drift.find_binary() == Path(os.path.realpath(real))


def test_find_binary_returns_path_claude_when_it_has_the_anchor(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("CLAUDE_CODE_EXECPATH", raising=False)
    bindir = tmp_path / "bin"
    bindir.mkdir()
    direct = bindir / "claude"
    _stub(direct, anchor=True)
    monkeypatch.setenv("PATH", str(bindir))
    assert drift.find_binary() == Path(os.path.realpath(direct))


def test_find_binary_resolves_the_path_claude_through_a_symlink(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The PATH branch must realpath its result too -- like the EXECPATH
    and .claude-wrapped branches -- so one physical binary keys the cache
    under one string regardless of which branch found it. The other two
    branches were pinned already; this one wasn't, because a plain
    (non-symlink) stub file can't distinguish `Path(found)` from
    `Path(realpath(found))`.
    """
    monkeypatch.delenv("CLAUDE_CODE_EXECPATH", raising=False)
    real = tmp_path / "claude-real"
    _stub(real, anchor=True)
    bindir = tmp_path / "bin"
    bindir.mkdir()
    link = bindir / "claude"
    link.symlink_to(real)
    monkeypatch.setenv("PATH", str(bindir))
    assert drift.find_binary() == real


def test_find_binary_rejects_execpath_naming_a_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """EXECPATH naming a directory must fall through to the PATH-based
    lookup, not be trusted as a binary -- is_file() rejects a directory
    where a weaker exists() check would not. The existing dangling-path
    test doesn't distinguish these: exists() rejects that case too.
    """
    a_directory = tmp_path / "not-a-binary"
    a_directory.mkdir()
    monkeypatch.setenv("CLAUDE_CODE_EXECPATH", str(a_directory))
    bindir = tmp_path / "bin"
    bindir.mkdir()
    direct = bindir / "claude"
    _stub(direct, anchor=True)
    monkeypatch.setenv("PATH", str(bindir))
    assert drift.find_binary() == Path(os.path.realpath(direct))


def test_find_binary_raises_without_execpath_or_path_claude(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("CLAUDE_CODE_EXECPATH", raising=False)
    monkeypatch.setenv("PATH", str(tmp_path))
    with pytest.raises(RuntimeError, match="not on PATH"):
        drift.find_binary()


def test_find_binary_falls_through_when_execpath_is_not_a_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A set-but-dangling CLAUDE_CODE_EXECPATH must not be trusted blindly --
    find_binary falls through to the PATH-based lookup instead of returning
    a path that names nothing.
    """
    monkeypatch.setenv("CLAUDE_CODE_EXECPATH", str(tmp_path / "does-not-exist"))
    bindir = tmp_path / "bin"
    bindir.mkdir()
    direct = bindir / "claude"
    _stub(direct, anchor=True)
    monkeypatch.setenv("PATH", str(bindir))
    assert drift.find_binary() == Path(os.path.realpath(direct))


def test_find_binary_raises_naming_execpath_when_set_but_not_a_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    dangling = tmp_path / "does-not-exist"
    monkeypatch.setenv("CLAUDE_CODE_EXECPATH", str(dangling))
    monkeypatch.setenv("PATH", str(tmp_path))  # empty dir, no `claude` either
    with pytest.raises(RuntimeError, match=re.escape(str(dangling))):
        drift.find_binary()


def test_find_binary_treats_an_empty_path_claude_as_no_anchor(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """mmap refuses to map a zero-length file; the anchor check must handle
    that without crashing, falling through exactly as a small non-anchor
    file would.
    """
    monkeypatch.delenv("CLAUDE_CODE_EXECPATH", raising=False)
    bindir = tmp_path / "bin"
    bindir.mkdir()
    empty = bindir / "claude"
    empty.write_bytes(b"")
    empty.chmod(0o755)
    monkeypatch.setenv("PATH", str(bindir))
    with pytest.raises(RuntimeError, match="no env-block anchor"):
        drift.find_binary()


def test_installed_version_parses_the_first_token(tmp_path: Path) -> None:
    binary = tmp_path / "claude"
    binary.write_text("#!/bin/sh\necho '2.1.235 (Claude Code)'\n")
    binary.chmod(0o755)
    assert drift.installed_version(binary) == "2.1.235"


def test_installed_version_raises_when_the_binary_exits_nonzero(
    tmp_path: Path,
) -> None:
    binary = tmp_path / "claude"
    binary.write_text("#!/bin/sh\necho 'boom' >&2\nexit 1\n")
    binary.chmod(0o755)
    with pytest.raises(RuntimeError, match="boom"):
        drift.installed_version(binary)


def test_installed_version_raises_on_empty_output(tmp_path: Path) -> None:
    binary = tmp_path / "claude"
    binary.write_text("#!/bin/sh\nexit 0\n")
    binary.chmod(0o755)
    with pytest.raises(RuntimeError, match="no output"):
        drift.installed_version(binary)


def test_installed_version_raises_on_timeout(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A blocked subprocess is the one failure Task 7's `except Exception`
    cannot absorb -- it converts a raise into a note, not a hang. Proven via
    a monkeypatched subprocess.run rather than a real multi-second sleep, so
    the suite stays fast.
    """
    binary = tmp_path / "claude"
    binary.write_text("#!/bin/sh\n")
    binary.chmod(0o755)

    def fake_run(
        *args: object, **kwargs: object
    ) -> subprocess.CompletedProcess[str]:
        assert kwargs["timeout"] == 10
        raise subprocess.TimeoutExpired(cmd=[str(binary), "--version"], timeout=10)

    monkeypatch.setattr(subprocess, "run", fake_run)
    with pytest.raises(RuntimeError, match="timed out"):
        drift.installed_version(binary)


ROOT = Path(__file__).resolve().parents[1]


def _run_hook(payload: str, env_overrides: dict[str, str]) -> dict[str, object]:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT / "src")
    env.update(env_overrides)
    result = subprocess.run(
        [sys.executable, "-m", "claude_config.env_context"],
        input=payload,
        capture_output=True,
        text=True,
        env=env,
        cwd=str(ROOT),
    )
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


def test_hook_emits_the_envelope(tmp_path: Path) -> None:
    payload = json.dumps(
        {
            "session_id": "abc-123",
            "transcript_path": "/dev/null",
            "cwd": str(ROOT),
            "hook_event_name": "SessionStart",
            "source": "startup",
            "model": "claude-opus-5",
        }
    )
    out = _run_hook(payload, {"CLAUDE_CODE_TMPDIR": str(tmp_path)})
    hook = out["hookSpecificOutput"]
    assert hook["hookEventName"] == "SessionStart"
    context = hook["additionalContext"]
    assert "# Environment" in context
    assert "# Scratchpad Directory" in context
    assert "You are powered by the model claude-opus-5" in context
    assert "Session ID: abc-123" in context
    # This repo's manifest is pinned against the installed binary (Task 5),
    # so a real, unmocked run against it must be drift-free. An independent
    # mutation sweep found drift_note()'s MANIFEST/CACHE arguments swapped
    # survived every existing test -- none of them asserted the happy path
    # has no NOTE bullet at all, so cached_note() misreading one file as the
    # other (and failing) looked the same as a clean, no-drift run.
    assert "NOTE:" not in context


def test_hook_omits_model_in_print_mode(tmp_path: Path) -> None:
    payload = json.dumps(
        {
            "session_id": "abc-123",
            "transcript_path": "/dev/null",
            "cwd": str(ROOT),
            "hook_event_name": "SessionStart",
            "source": "startup",
        }
    )
    out = _run_hook(payload, {"CLAUDE_CODE_TMPDIR": str(tmp_path)})
    assert "powered by the model" not in out["hookSpecificOutput"]["additionalContext"]


def test_hook_creates_the_scratchpad(tmp_path: Path) -> None:
    payload = json.dumps(
        {
            "session_id": "xyz-789",
            "transcript_path": "/dev/null",
            "cwd": str(ROOT),
            "hook_event_name": "SessionStart",
            "source": "startup",
        }
    )
    _run_hook(payload, {"CLAUDE_CODE_TMPDIR": str(tmp_path)})
    created = list(tmp_path.glob(f"claude-{os.getuid()}/*/xyz-789/scratchpad"))
    assert len(created) == 1
    assert created[0].is_dir()


def test_hook_fails_loudly_on_malformed_payload() -> None:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT / "src")
    result = subprocess.run(
        [sys.executable, "-m", "claude_config.env_context"],
        input="not json",
        capture_output=True,
        text=True,
        env=env,
        cwd=str(ROOT),
    )
    assert result.returncode != 0
    assert "Traceback" in result.stderr


def test_scratchpad_none_when_it_cannot_be_created(tmp_path: Path) -> None:
    """A cwd past cc's slug limit must cost the section, not the block."""
    deep = tmp_path / ("d" * 120) / ("e" * 120)
    deep.mkdir(parents=True)
    payload = json.dumps(
        {
            "session_id": "abc-123",
            "transcript_path": "/dev/null",
            "cwd": str(deep),
            "hook_event_name": "SessionStart",
            "source": "startup",
        }
    )
    out = _run_hook(payload, {"CLAUDE_CODE_TMPDIR": str(tmp_path)})
    context = out["hookSpecificOutput"]["additionalContext"]
    assert "# Environment" in context
    assert "# Scratchpad Directory" not in context


def test_shell_fallback_when_no_shell_resolves(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """A shell that cannot be named must not cost the session its whole
    block -- and cc's own bare "unknown" is the wrong fallback text: it is
    indistinguishable from cc's own degenerate default and discards the one
    actionable fact this hook could report, leaving it only on stderr, which
    is not something the agent reads.
    """
    from claude_config.env_context import __main__ as entry

    def boom() -> str:
        raise RuntimeError("no bash or zsh found")

    monkeypatch.setattr(entry.environment, "resolve_shell", boom)
    assert entry.resolved_shell() == (
        "none found — no bash or zsh on this system, so Bash tool calls will fail"
    )
    assert "no bash or zsh found" in capsys.readouterr().err


def test_hook_suppresses_scratchpad_in_background_session(tmp_path: Path) -> None:
    """The bg gate must short-circuit before scratchpad.ensure runs, not just
    drop the rendered section afterwards -- otherwise a background session
    still gets a directory on disk that nothing in its prompt names, and the
    two-instruction conflict this gate exists to prevent shows up one layer
    down instead of going away.
    """
    payload = json.dumps(
        {
            "session_id": "bg-123",
            "transcript_path": "/dev/null",
            "cwd": str(ROOT),
            "hook_event_name": "SessionStart",
            "source": "startup",
        }
    )
    out = _run_hook(
        payload,
        {"CLAUDE_CODE_TMPDIR": str(tmp_path), "CLAUDE_CODE_SESSION_KIND": "bg"},
    )
    context = out["hookSpecificOutput"]["additionalContext"]
    assert "# Environment" in context
    assert "# Scratchpad Directory" not in context
    assert list(tmp_path.rglob("*")) == []


def test_root_manifest_and_cache_paths() -> None:
    """Pins the three module-level path constants directly. An independent
    mutation sweep found ROOT walking parents[2] instead of [3], and wrong
    MANIFEST/CACHE filenames -- invisible to every subprocess test, since
    none of them assert on these constants at all.
    """
    from claude_config.env_context import __main__ as entry

    assert entry.ROOT == ROOT
    assert entry.MANIFEST == ROOT / "docs" / "env-context-manifest.json"
    assert entry.CACHE == Path.home() / ".claude" / "env-context-drift.json"


def test_main_wires_every_collaborator_into_its_own_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An in-process companion the subprocess tests cannot provide: a
    subprocess cannot inject a fixture, so main()'s facts dict had zero
    coverage of which value lands under which key. An independent mutation
    sweep found two concrete failures of exactly this kind: shell and
    os_version's call sites swapped (the block can report `Shell: <the OS
    version>` / `OS Version: <the shell path>`), and, separately, deleting
    drift_note() entirely and hardcoding "drift_note": None in main() --
    with every subprocess test still green either way, because none of them
    assert a specific value behind any of these labels. Monkeypatching every
    collaborator to its own distinguishable sentinel and asserting each
    lands under its own key catches both, and any other misassignment
    among them.
    """
    from claude_config.env_context import __main__ as entry

    captured: dict[str, object] = {}

    def fake_sections(facts: render.Facts) -> str:
        captured.update(facts)
        return "stub"

    monkeypatch.setattr(entry.environment, "is_git_repo", lambda cwd: "SENTINEL-GITREPO")
    monkeypatch.setattr(
        entry.environment, "worktree_common_dir", lambda cwd: "SENTINEL-WORKTREE"
    )
    monkeypatch.setattr(entry.environment, "platform_name", lambda: "SENTINEL-PLATFORM")
    monkeypatch.setattr(entry.environment, "os_version", lambda: "SENTINEL-OSVER")
    monkeypatch.setattr(entry, "resolved_shell", lambda: "SENTINEL-SHELL")
    monkeypatch.setattr(
        entry, "scratchpad_or_none", lambda cwd, session_id: "SENTINEL-SCRATCHPAD"
    )
    monkeypatch.setattr(entry, "drift_note", lambda: "SENTINEL-DRIFT")
    monkeypatch.setattr(render, "sections", fake_sections)
    monkeypatch.setattr(
        sys, "stdin", io.StringIO(json.dumps({"cwd": "/tmp", "session_id": "s1"}))
    )

    assert entry.main() == 0

    assert captured["cwd"] == "/tmp"
    assert captured["session_id"] == "s1"
    assert captured["is_git_repo"] == "SENTINEL-GITREPO"
    assert captured["worktree_common_dir"] == "SENTINEL-WORKTREE"
    assert captured["platform"] == "SENTINEL-PLATFORM"
    assert captured["os_version"] == "SENTINEL-OSVER"
    assert captured["shell"] == "SENTINEL-SHELL"
    assert captured["scratchpad"] == "SENTINEL-SCRATCHPAD"
    assert captured["drift_note"] == "SENTINEL-DRIFT"


def test_drift_note_returns_the_cached_note_value_unchanged(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The pass-through branch: whatever cached_note() returns is what
    drift_note() returns, verbatim. Uses a sentinel distinguishable from
    None so that a drift_note() body which stopped calling cached_note --
    or started ignoring its result -- fails here rather than reading as a
    clean "no drift" result.
    """
    from claude_config.env_context import __main__ as entry

    monkeypatch.setattr(entry.drift, "find_binary", lambda: Path("/fake/claude"))
    monkeypatch.setattr(
        entry.drift,
        "cached_note",
        lambda binary, manifest, cache: "SENTINEL-DRIFT-NOTE",
    )
    assert entry.drift_note() == "SENTINEL-DRIFT-NOTE"


def test_drift_note_surfaces_a_failure_when_the_check_itself_breaks(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Closes the blind spot review finding 2 warned about: except Exception
    is the right clause for cached_note (it stats, reads a 331 MB binary,
    spawns a subprocess, and parses two JSON files -- any narrower tuple
    would be Exception minus programming errors), but nothing proved it
    actually fires. Simulates the reviewer's own example -- drift.cached_note
    renamed -- via delattr, and pins that the resulting note names both the
    exception's type (a bare exception message reads as gibberish) and an
    absolute, repo-rooted script path (a repo-relative one names no repo,
    and the hook runs from whatever cwd the session started in).
    """
    from claude_config.env_context import __main__ as entry

    monkeypatch.setattr(entry.drift, "find_binary", lambda: Path("/fake/claude"))
    monkeypatch.delattr(entry.drift, "cached_note")

    note = entry.drift_note()

    assert note is not None
    assert "AttributeError" in note
    assert "cached_note" in note
    assert str(entry.ROOT / "scripts" / "check-env-context.sh") in note
    assert "AttributeError" in capsys.readouterr().err


def test_scratchpad_or_none_prints_to_stderr_when_it_cannot_be_created(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """An independent mutation sweep found this print(..., file=sys.stderr)
    line deletable: every subprocess test that hits this branch only checks
    the rendered block, never stderr. stderr from a hook is not something
    the agent reads, but it is something a human debugging the hook does.
    """
    from claude_config.env_context import __main__ as entry

    def boom(**kwargs: object) -> Path:
        raise ValueError("simulated: session_id rejected")

    monkeypatch.setattr(entry.scratchpad, "ensure", boom)

    result = entry.scratchpad_or_none("/tmp", "s1", env={})

    assert result is None
    assert "env-context: scratchpad unavailable" in capsys.readouterr().err


def test_scratchpad_or_none_suppressed_by_injected_env_without_a_subprocess(
    tmp_path: Path,
) -> None:
    """The payoff of threading env through scratchpad_or_none (review finding
    7): the background-session gate is now exercisable with a plain dict,
    in-process, instead of only via a subprocess whose real environment
    happens to carry the variable. This is a faster companion to
    test_hook_suppresses_scratchpad_in_background_session above, not a
    replacement -- that one still proves the real subprocess path works.
    """
    from claude_config.env_context import __main__ as entry

    result = entry.scratchpad_or_none(
        str(ROOT),
        "session-in-process",
        env={"CLAUDE_CODE_SESSION_KIND": "bg", "CLAUDE_CODE_TMPDIR": str(tmp_path)},
    )

    assert result is None
    assert list(tmp_path.rglob("*")) == []


def test_scratchpad_or_none_actually_uses_the_injected_env(tmp_path: Path) -> None:
    """Confirms env is forwarded on to scratchpad.ensure, not merely
    consulted for the bg gate above. Without the forward, ensure() falls
    back to its own os.environ default for CLAUDE_CODE_TMPDIR, so the
    scratchpad would land under the real /tmp instead of under the tmp_path
    this test injects -- the bg-gate test above can't tell the difference,
    since CLAUDE_CODE_SESSION_KIND == "bg" returns before ensure() is ever
    reached.
    """
    from claude_config.env_context import __main__ as entry

    result = entry.scratchpad_or_none(
        str(ROOT), "session-env-forward", env={"CLAUDE_CODE_TMPDIR": str(tmp_path)}
    )

    assert result is not None
    assert result.startswith(str(tmp_path))
    created = list(
        tmp_path.glob(f"claude-{os.getuid()}/*/session-env-forward/scratchpad")
    )
    assert len(created) == 1


def _run_hook_expecting_exit(payload: str) -> subprocess.CompletedProcess[str]:
    """Like _run_hook, but for payloads the hook must reject -- returns the
    raw CompletedProcess since the caller needs returncode and stderr, not a
    parsed envelope that was never produced.
    """
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT / "src")
    return subprocess.run(
        [sys.executable, "-m", "claude_config.env_context"],
        input=payload,
        capture_output=True,
        text=True,
        env=env,
        cwd=str(ROOT),
    )


def test_missing_cwd_exits_loudly_naming_the_contract() -> None:
    """A missing key means Claude Code's own hook payload contract changed --
    exactly the drift class this feature exists to catch -- so it must be
    loud: a clean SystemExit message naming the contract, not an incidental
    KeyError traceback raised three calls downstream.
    """
    result = _run_hook_expecting_exit(json.dumps({"session_id": "s1"}))
    assert result.returncode != 0
    assert "missing field 'cwd'" in result.stderr
    assert "Traceback" not in result.stderr


def test_missing_session_id_exits_loudly_naming_the_contract() -> None:
    result = _run_hook_expecting_exit(json.dumps({"cwd": str(ROOT)}))
    assert result.returncode != 0
    assert "missing field 'session_id'" in result.stderr
    assert "Traceback" not in result.stderr


def test_wrong_type_cwd_exits_loudly_naming_the_contract() -> None:
    """Measured: before this guard, cwd: 99 reached a bare TypeError three
    calls deep (inside subprocess.run's cwd handling) instead of failing
    here, at the point the contract was actually violated, with a message
    that names it.
    """
    result = _run_hook_expecting_exit(json.dumps({"cwd": 99, "session_id": "s1"}))
    assert result.returncode != 0
    assert "field 'cwd' is int, expected str" in result.stderr
    assert "Traceback" not in result.stderr


def test_wrong_type_session_id_exits_loudly_naming_the_contract() -> None:
    result = _run_hook_expecting_exit(
        json.dumps({"cwd": str(ROOT), "session_id": 12345})
    )
    assert result.returncode != 0
    assert "field 'session_id' is int, expected str" in result.stderr
    assert "Traceback" not in result.stderr


def test_model_absent_is_accepted_by_the_type_check(tmp_path: Path) -> None:
    """The first of the three cases _optional_str must get right: a payload
    with no "model" key at all -- print mode's normal shape -- must render
    cleanly with no model line, not raise.
    """
    payload = json.dumps(
        {
            "session_id": "abc-123",
            "transcript_path": "/dev/null",
            "cwd": str(ROOT),
            "hook_event_name": "SessionStart",
            "source": "startup",
        }
    )
    out = _run_hook(payload, {"CLAUDE_CODE_TMPDIR": str(tmp_path)})
    context = out["hookSpecificOutput"]["additionalContext"]
    assert "# Environment" in context
    assert "powered by the model" not in context


def test_model_none_is_accepted_by_the_type_check(tmp_path: Path) -> None:
    """The second case: an explicit JSON null must degrade the same quiet
    way absence does, not be treated as a wrong-typed value.
    """
    payload = json.dumps(
        {
            "session_id": "abc-123",
            "transcript_path": "/dev/null",
            "cwd": str(ROOT),
            "hook_event_name": "SessionStart",
            "source": "startup",
            "model": None,
        }
    )
    out = _run_hook(payload, {"CLAUDE_CODE_TMPDIR": str(tmp_path)})
    context = out["hookSpecificOutput"]["additionalContext"]
    assert "# Environment" in context
    assert "powered by the model" not in context


def test_wrong_type_model_exits_loudly_naming_the_contract() -> None:
    """The third case, and the one with no guard at all before this fix:
    measured, a payload carrying {"model": {"id": "x"}} used to render
    " - You are powered by the model {'id': 'x'}" -- a Python repr inside
    the prompt -- instead of failing here, because the old
    `cast("str | None", ...)` performs no runtime check at all.
    """
    result = _run_hook_expecting_exit(
        json.dumps({"cwd": str(ROOT), "session_id": "s1", "model": {"id": "x"}})
    )
    assert result.returncode != 0
    assert "field 'model' is dict, expected str" in result.stderr
    assert "Traceback" not in result.stderr


def test_empty_cwd_and_session_id_degrade_quietly(tmp_path: Path) -> None:
    """The other side of the boundary review finding 4 draws: a merely-empty
    string is parseable and degenerate, not a breach of the contract's
    shape, so it degrades quietly through the existing scratchpad guard
    instead of exiting -- unlike the wrong-type case above, which must be
    loud.
    """
    payload = json.dumps(
        {
            "session_id": "",
            "transcript_path": "/dev/null",
            "cwd": "",
            "hook_event_name": "SessionStart",
            "source": "startup",
        }
    )
    out = _run_hook(payload, {"CLAUDE_CODE_TMPDIR": str(tmp_path)})
    context = out["hookSpecificOutput"]["additionalContext"]
    assert "# Environment" in context
    assert "# Scratchpad Directory" not in context


# --- git snapshot ----------------------------------------------------------
#
# cc's own gitStatus reminder is gated together with the Bash tool's git block
# by `includeGitInstructions`, and a -p session never carries it at all. This
# is the copy that survives both, so these pin what it reports and how.


def test_git_snapshot_none_outside_repo(tmp_path: Path) -> None:
    assert environment.git_snapshot(str(tmp_path)) is None


def test_git_snapshot_reports_branch_status_and_recent_commits(tmp_path: Path) -> None:
    _init_repo(tmp_path)

    def run(*args: str) -> str:
        return subprocess.run(
            args, cwd=tmp_path, check=True, capture_output=True, text=True
        ).stdout

    (tmp_path / "a.txt").write_text("x\n")
    run("git", "add", "a.txt")
    run("git", "-c", "commit.gpgsign=false", "commit", "-qm", "add a")
    (tmp_path / "a.txt").write_text("y\n")  # modified, unstaged
    (tmp_path / "b.txt").write_text("z\n")  # untracked

    snap = environment.git_snapshot(str(tmp_path))

    assert snap is not None
    assert snap["branch"] == run("git", "branch", "--show-current").strip()
    assert snap["status"].splitlines() == [" M a.txt", "?? b.txt"]
    commits = snap["recent_commits"].splitlines()
    assert len(commits) == 2
    assert commits[0].endswith(" add a") and commits[1].endswith(" init")


def test_git_snapshot_status_is_capped_like_cc(tmp_path: Path) -> None:
    """cc cuts its own status output at 2000 characters; a tree with hundreds
    of untracked files must cost a marker line, not the rest of the prompt."""
    _init_repo(tmp_path)
    for i in range(400):
        (tmp_path / f"untracked-{i:04d}.txt").write_text("")

    snap = environment.git_snapshot(str(tmp_path))

    assert snap is not None
    assert snap["status"].endswith(environment.STATUS_TRUNCATED)
    body = snap["status"][: -len(environment.STATUS_TRUNCATED)]
    assert len(body) == environment.STATUS_CAP


def test_git_status_section_renders_branch_status_and_commits() -> None:
    text = render.sections(
        _facts(
            git_snapshot={
                "branch": "main",
                "status": " M notes.txt",
                "recent_commits": "abc1234 Add greet and notes",
            }
        )
    )
    assert text.endswith(
        "\n\n# Git status at session start\n"
        "Current branch: main\n\n"
        "Status:\n M notes.txt\n\n"
        "Recent commits:\nabc1234 Add greet and notes"
    )


def test_git_status_section_names_clean_tree_and_empty_history() -> None:
    text = render.sections(
        _facts(git_snapshot={"branch": "main", "status": "", "recent_commits": ""})
    )
    assert "Status:\n(clean)\n" in text
    assert text.endswith("Recent commits:\n(none)")


def test_git_status_section_omitted_without_a_snapshot() -> None:
    assert "Git status" not in render.sections(_facts(git_snapshot=None))
    assert "Git status" not in render.sections(_facts())
