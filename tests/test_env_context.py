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
