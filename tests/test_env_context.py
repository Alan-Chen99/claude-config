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


from claude_config.env_context import render


def _facts(**overrides: object) -> dict[str, object]:
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
    return base


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
    assert " - This is a git worktree of /repos/claude-config/.git." in linked
    assert "git stash" in linked


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
