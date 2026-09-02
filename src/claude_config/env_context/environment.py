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
from collections.abc import Mapping

SEARCH_DIRS = ["/bin", "/usr/bin", "/usr/local/bin", "/opt/homebrew/bin"]


def _executable(path: str) -> bool:
    return os.path.isfile(path) and os.access(path, os.X_OK)


def resolve_shell(
    env: Mapping[str, str] | None = None,
    search_dirs: list[str] | None = None,
    found: dict[str, str | None] | None = None,
) -> str:
    """Return the shell the Bash tool will run, mirroring globals/10.js:22633.

    `found` maps a shell name to its PATH lookup, defaulting to shutil.which.
    Tests pass an explicit mapping to keep the real PATH out of the result.
    """
    env = os.environ if env is None else env
    search_dirs = SEARCH_DIRS if search_dirs is None else search_dirs
    if found is None:
        found = {"zsh": shutil.which("zsh"), "bash": shutil.which("bash")}

    override = env.get("CLAUDE_CODE_SHELL")
    if override and ("bash" in override or "zsh" in override) and _executable(override):
        return override

    shell = env.get("SHELL")
    named_valid = bool(shell) and ("bash" in shell or "zsh" in shell)
    prefers_bash = bool(shell) and "bash" in shell

    order = ["bash", "zsh"] if prefers_bash else ["zsh", "bash"]
    candidates = [f"{d}/{name}" for name in order for d in search_dirs]

    preferred, other = ("bash", "zsh") if prefers_bash else ("zsh", "bash")
    if preferred_path := found.get(preferred):
        candidates.insert(0, preferred_path)
    if other_path := found.get(other):
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


def is_git_repo(cwd: str) -> bool:
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        cwd=cwd,
        capture_output=True,
        text=True,
    )
    return result.returncode == 0


def worktree_common_dir(cwd: str) -> str | None:
    """Return the shared git dir when cwd is a linked worktree, else None.

    Claude Code emits its worktree warnings only for worktrees it created
    itself (`cv()`, globals/04.js:7126), so it stays silent in one made by
    hand. Asking git directly covers both.
    """
    result = subprocess.run(
        ["git", "rev-parse", "--path-format=absolute", "--git-dir", "--git-common-dir"],
        cwd=cwd,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return None
    lines = result.stdout.split("\n")
    if len(lines) < 2:
        return None
    git_dir, common_dir = lines[0].strip(), lines[1].strip()
    if not git_dir or not common_dir or git_dir == common_dir:
        return None
    return common_dir


def os_version() -> str:
    """Mirrors os.type() + ' ' + os.release() (`Yml()`, globals/21.js:13572)."""
    return f"{platform.system()} {platform.release()}"


def platform_name() -> str:
    return sys.platform
