"""Machine facts for the env block.

Claude Code's own env block reports `$SHELL`, falling back to the literal
string `unknown` (`Kml()`, globals/21.js:13560). That is not the shell it runs
commands with: the Bash tool resolves one independently (globals/10.js:22633)
and exports it. `resolve_shell` mirrors the Bash tool, so the reported shell is
the one Bash tool commands execute under.
"""

from __future__ import annotations

import os
import platform
import shutil
import subprocess
import sys
from collections.abc import Callable, Mapping, Sequence

SEARCH_DIRS: tuple[str, ...] = ("/bin", "/usr/bin", "/usr/local/bin", "/opt/homebrew/bin")


def _executable(path: str) -> bool:
    return os.path.isfile(path) and os.access(path, os.X_OK)


def resolve_shell(
    env: Mapping[str, str] | None = None,
    search_dirs: Sequence[str] | None = None,
    found: Callable[[str], str | None] = shutil.which,
) -> str:
    """Return the shell the Bash tool will run, mirroring globals/10.js:22633.

    `found` looks up a shell name on PATH, defaulting to shutil.which. Tests
    pass a stub (e.g. `lambda _: None`) to keep the real PATH out of the result.
    """
    env = os.environ if env is None else env
    search_dirs = SEARCH_DIRS if search_dirs is None else search_dirs

    override = env.get("CLAUDE_CODE_SHELL")
    if override and ("bash" in override or "zsh" in override) and _executable(override):
        return override

    shell = env.get("SHELL")
    named_valid = bool(shell) and ("bash" in shell or "zsh" in shell)
    prefers_bash = bool(shell) and "bash" in shell

    order = ["bash", "zsh"] if prefers_bash else ["zsh", "bash"]
    candidates = [f"{d}/{name}" for name in order for d in search_dirs]

    preferred, other = ("bash", "zsh") if prefers_bash else ("zsh", "bash")
    if preferred_path := found(preferred):
        candidates.insert(0, preferred_path)
    if other_path := found(other):
        candidates.append(other_path)
    if named_valid and shell and _executable(shell):
        candidates.insert(0, shell)

    for candidate in candidates:
        if _executable(candidate):
            return candidate

    raise RuntimeError(
        "no bash or zsh found; searched "
        + f"{', '.join(search_dirs)} and PATH. Claude Code's Bash tool would fail too."
    )


def _git(args: Sequence[str], cwd: str) -> subprocess.CompletedProcess[str] | None:
    """Run git, or return None when it could not run at all.

    A missing git binary, a deleted cwd and a cwd that is a file all raise
    rather than exiting non-zero. The hook must still produce a block, so an
    unrunnable git reads the same as "not a repository".
    """
    try:
        return subprocess.run(
            ["git", *args], cwd=cwd, capture_output=True, text=True, timeout=5
        )
    except (OSError, subprocess.SubprocessError):
        return None


def is_git_repo(cwd: str) -> bool:
    result = _git(["rev-parse", "--show-toplevel"], cwd)
    return result is not None and result.returncode == 0


def worktree_common_dir(cwd: str) -> str | None:
    """Return the shared git dir when cwd is a linked worktree, else None.

    Claude Code emits its worktree warnings only for worktrees it created
    itself (`cv()`, globals/04.js:7126), so it stays silent in one made by
    hand. Asking git directly covers both.
    """
    result = _git(
        ["rev-parse", "--path-format=absolute", "--git-dir", "--git-common-dir"], cwd
    )
    if result is None or result.returncode != 0:
        return None
    lines = result.stdout.split("\n")
    if len(lines) < 2:
        return None
    git_dir, common_dir = lines[0].strip(), lines[1].strip()
    if not git_dir or not common_dir or git_dir == common_dir:
        return None
    return common_dir


def os_version() -> str:
    """Mirrors os.type() + ' ' + os.release() (`Yml()`, globals/21.js:13572; POSIX branch)."""
    return f"{platform.system()} {platform.release()}"


def platform_name() -> str:
    """Node's `process.platform` and Python's `sys.platform` agree on the names
    that matter here: `linux`, `darwin`, `win32`.
    """
    return sys.platform
