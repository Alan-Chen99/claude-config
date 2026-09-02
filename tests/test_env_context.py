"""Tests for the env-context SessionStart hook."""

import importlib


def test_package_imports() -> None:
    module = importlib.import_module("claude_config.env_context")
    assert module.__file__ is not None
    assert module.__file__.endswith("__init__.py")


from pathlib import Path

from claude_config.env_context import environment


def _fake_tree(root: Path, shells: list[str]) -> None:
    """Create executable stubs at the given absolute-looking paths under root."""
    for rel in shells:
        target = root / rel.lstrip("/")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("#!/bin/sh\n")
        target.chmod(0o755)


def test_shell_override_wins(tmp_path: Path) -> None:
    _fake_tree(tmp_path, ["/opt/custom/bash", "/bin/zsh"])
    result = environment.resolve_shell(
        env={"CLAUDE_CODE_SHELL": str(tmp_path / "opt/custom/bash")},
        search_dirs=[str(tmp_path / "bin")],
        found={},
    )
    assert result == str(tmp_path / "opt/custom/bash")


def test_shell_override_ignored_when_not_bash_or_zsh(tmp_path: Path) -> None:
    _fake_tree(tmp_path, ["/opt/custom/fish", "/bin/zsh"])
    result = environment.resolve_shell(
        env={"CLAUDE_CODE_SHELL": str(tmp_path / "opt/custom/fish")},
        search_dirs=[str(tmp_path / "bin")],
        found={},
    )
    assert result == str(tmp_path / "bin/zsh")


def test_zsh_preferred_when_shell_unset(tmp_path: Path) -> None:
    _fake_tree(tmp_path, ["/bin/bash", "/bin/zsh"])
    result = environment.resolve_shell(
        env={},
        search_dirs=[str(tmp_path / "bin")],
        found={},
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
        found={},
    )
    assert result == str(tmp_path / "bin/bash")


def test_falls_back_to_bash_when_no_zsh(tmp_path: Path) -> None:
    _fake_tree(tmp_path, ["/bin/bash"])
    result = environment.resolve_shell(
        env={},
        search_dirs=[str(tmp_path / "bin")],
        found={},
    )
    assert result == str(tmp_path / "bin/bash")


def test_raises_when_no_shell_exists(tmp_path: Path) -> None:
    (tmp_path / "bin").mkdir()
    try:
        environment.resolve_shell(env={}, search_dirs=[str(tmp_path / "bin")], found={})
    except RuntimeError as exc:
        assert "no bash or zsh" in str(exc).lower()
    else:
        raise AssertionError("expected RuntimeError")
