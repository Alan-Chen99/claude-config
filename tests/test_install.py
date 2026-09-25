import os
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]

# install.sh reaches its linking steps with only these on PATH. cargo, uv and
# systemctl are absent on purpose: those steps are skipped with a warning, so a
# run costs no build.
STUB_COMMANDS = ("basename", "dirname", "git", "ln", "mkdir")


def _install_env(tmp_path: Path) -> tuple[dict[str, str], Path]:
    home = tmp_path / "home"
    home.mkdir()
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    for command in STUB_COMMANDS:
        resolved = shutil.which(command)
        assert resolved is not None, f"{command} is not on PATH"
        (bin_dir / command).symlink_to(resolved)

    env = os.environ.copy()
    env["HOME"] = str(home)
    env["PATH"] = str(bin_dir)
    env.pop("ALLOW_WORKTREE_INSTALL", None)
    return env, home


def _run(script: Path, cwd: Path, env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["/bin/bash", str(script)],
        cwd=cwd,
        env=env,
        text=True,
        capture_output=True,
    )


def test_install_links_opencode_config(tmp_path: Path) -> None:
    env, home = _install_env(tmp_path)

    result = _run(ROOT / "install.sh", ROOT, env)
    assert result.returncode == 0, result.stderr

    opencode_link = home / ".config" / "opencode"
    assert opencode_link.is_symlink()
    assert opencode_link.resolve() == ROOT / "opencode"


@pytest.mark.parametrize("decoy_git", [False, True], ids=["plain-cwd", "cwd-with-git-dir"])
def test_install_runs_from_any_cwd(tmp_path: Path, decoy_git: bool) -> None:
    """The install target is the script's own checkout, whatever $PWD is.

    A cwd holding its own .git is the sharper case: resolving git's relative
    path output against $PWD reads that repository instead of this one.
    """
    env, home = _install_env(tmp_path)
    cwd = tmp_path / "elsewhere"
    cwd.mkdir()
    if decoy_git:
        (cwd / ".git").mkdir()

    result = _run(ROOT / "install.sh", cwd, env)
    assert result.returncode == 0, result.stderr

    assert (home / ".claude" / "skills").resolve() == ROOT / "skills"


def _worktree_of_this_script(tmp_path: Path) -> tuple[Path, Path]:
    """A throwaway repository holding install.sh, plus a worktree of it."""
    main = tmp_path / "main"
    subprocess.run(["git", "init", "-q", "-b", "main", str(main)], check=True)
    shutil.copy(ROOT / "install.sh", main / "install.sh")
    git = [
        "git",
        "-C",
        str(main),
        "-c",
        "user.email=test@example.invalid",
        "-c",
        "user.name=test",
        "-c",
        "commit.gpgsign=false",
    ]
    subprocess.run([*git, "add", "install.sh"], check=True)
    subprocess.run([*git, "commit", "-qm", "install script"], check=True)
    worktree = tmp_path / "wt"
    subprocess.run([*git, "worktree", "add", "-q", "-b", "wt", str(worktree)], check=True)
    return main, worktree


@pytest.mark.parametrize("cwd_name", ["worktree", "main", "neither"])
def test_install_refuses_from_worktree_whatever_the_cwd(tmp_path: Path, cwd_name: str) -> None:
    env, home = _install_env(tmp_path)
    main, worktree = _worktree_of_this_script(tmp_path)
    cwd = {"worktree": worktree, "main": main, "neither": tmp_path}[cwd_name]

    result = _run(worktree / "install.sh", cwd, env)
    assert result.returncode == 1
    assert "refusing to install from a worktree" in result.stderr
    assert not (home / ".claude").exists()


def test_install_escape_hatch_allows_worktree(tmp_path: Path) -> None:
    env, home = _install_env(tmp_path)
    env["ALLOW_WORKTREE_INSTALL"] = "1"
    _, worktree = _worktree_of_this_script(tmp_path)

    result = _run(worktree / "install.sh", tmp_path, env)
    assert result.returncode == 0, result.stderr
    assert (home / ".claude").is_dir()
