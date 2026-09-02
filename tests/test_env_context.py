"""Tests for the env-context SessionStart hook."""

import importlib


def test_package_imports() -> None:
    module = importlib.import_module("claude_config.env_context")
    assert module.__file__ is not None
    assert module.__file__.endswith("__init__.py")


import subprocess
from pathlib import Path

import pytest

from claude_config.env_context import environment


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


def test_os_version_returns_nonempty_string() -> None:
    result = environment.os_version()
    assert isinstance(result, str)
    assert result != ""


def test_platform_name_returns_nonempty_string() -> None:
    result = environment.platform_name()
    assert isinstance(result, str)
    assert result != ""


import stat

from claude_config.env_context import scratchpad


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


from typing import cast

from claude_config.env_context import render


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


import json
import os
import re

from claude_config.env_context import drift


def _binary(
    tmp_path: Path,
    literals: list[str],
    before: list[str] | None = None,
    far: list[str] | None = None,
) -> Path:
    """A stand-in binary: padding, optional pre-anchor literals, the anchor,
    post-anchor literals, then far strings.

    `before` mirrors production: in the real 2.1.235 binary, 12 of the 13
    pinned window literals sit *before* the anchor (measured offsets -32 to
    -1232) and only the anchor itself sits at offset 0 -- a fixture that
    places everything after the anchor never exercises WINDOW_BEFORE at
    all. `far` lands well past the scan window, standing in for the
    string-table region `Kml()`'s literals occupy in the real binary.
    """
    blob = b"\x00" * 100
    for text in before or []:
        blob += text.encode() + b"\x00"
    blob += b"You have been invoked in the following environment: "
    for text in literals:
        blob += b"\x00" + text.encode()
    blob += b"\x00" * 8000
    for text in far or []:
        blob += b"\x00" + text.encode()
    path = tmp_path / "claude.exe"
    path.write_bytes(blob)
    return path


def _manifest(tmp_path: Path, window: list[str], required: dict[str, int]) -> Path:
    """`_binary()` always writes the anchor, so a manifest that can ever
    truly match one must always list it too -- centralized here rather than
    repeated as a comment at each call site.
    """
    path = tmp_path / "manifest.json"
    path.write_text(
        json.dumps(
            {
                "version": "2.1.235",
                "window_literals": sorted({*window, drift.ANCHOR.decode()}),
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


def test_extract_raises_without_anchor(tmp_path: Path) -> None:
    path = tmp_path / "not-claude"
    path.write_bytes(b"nothing here")
    try:
        drift.extract_literals(path)
    except RuntimeError as exc:
        assert "anchor" in str(exc)
    else:
        raise AssertionError("expected RuntimeError")


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


def test_cached_note_text_names_the_script(tmp_path: Path) -> None:
    binary = _binary(tmp_path, ["Current sandbox mode: "])
    manifest = _manifest(tmp_path, ["Old field: "], {})
    cache = tmp_path / "cache.json"
    note = drift.cached_note(binary, manifest, cache, lambda: "2.1.240")
    assert note is not None
    assert "2.1.240" in note
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
        raise subprocess.TimeoutExpired(cmd=[str(binary), "--version"], timeout=5)

    monkeypatch.setattr(subprocess, "run", fake_run)
    with pytest.raises(RuntimeError, match="timed out"):
        drift.installed_version(binary)
