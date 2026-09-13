"""Machine facts for the env block.

Claude Code's own env block reports `$SHELL`, falling back to the literal
string `unknown` (`vWr()`, chunk-dbb93264.js:29150). That is not the shell it
runs commands with: the Bash tool resolves one independently (`das()`,
chunk-dbb93264.js:134358) and exports it. `resolve_shell` mirrors the Bash
tool, so the reported shell is the one Bash tool commands execute under.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from collections.abc import Callable, Mapping, Sequence
from typing import TypedDict

SEARCH_DIRS: tuple[str, ...] = ("/bin", "/usr/bin", "/usr/local/bin", "/opt/homebrew/bin")


def _executable(path: str) -> bool:
    """Whether `path` names something runnable, mirroring `cbt()`,
    chunk-dbb93264.js:134345.

    The access check answers for a real path; cc falls back to running the
    candidate with `--version` when it fails, which is what makes a bare
    `CLAUDE_CODE_SHELL=bash` resolve through PATH. Without the fallback this
    module ignores an override the Bash tool obeys and reports a shell that
    is not the one commands run under. Cost: `drift.py`'s timeout budget.
    """
    if os.path.isfile(path) and os.access(path, os.X_OK):
        return True
    try:
        probe = subprocess.run(
            [path, "--version"], capture_output=True, timeout=1, check=False
        )
    except (OSError, subprocess.SubprocessError):
        return False
    return probe.returncode == 0


def resolve_shell(
    env: Mapping[str, str] | None = None,
    search_dirs: Sequence[str] | None = None,
    found: Callable[[str], str | None] = shutil.which,
) -> str:
    """Return the shell the Bash tool will run, mirroring `das()`,
    chunk-dbb93264.js:134358.

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

    `timeout=2`: this is called up to five times per hook run (is_git_repo,
    worktree_common_dir, then git_snapshot's three reads), so a hung git
    costs up to 5x this value before the hook can move on. It shares the settings.json SessionStart hook's 30 s
    budget with drift.installed_version's own subprocess call -- see that
    function's docstring for the full arithmetic across all three numbers.
    """
    try:
        return subprocess.run(
            ["git", *args], cwd=cwd, capture_output=True, text=True, timeout=2
        )
    except (OSError, subprocess.SubprocessError):
        return None


def is_git_repo(cwd: str) -> bool:
    result = _git(["rev-parse", "--show-toplevel"], cwd)
    return result is not None and result.returncode == 0


def worktree_common_dir(cwd: str) -> str | None:
    """Return the shared git dir when cwd is a linked worktree, else None.

    Asking git directly is what covers a worktree made by hand. Through
    2.1.235 that was the whole point: cc emitted its worktree warnings only
    for worktrees it had created itself. 2.1.269 broadened its own test to
    `pP()` (chunk-arxpc433.js:1653) -- git-common-dir differs from git-dir,
    the same question this asks -- so the two now agree on which directories
    count, and this no longer covers a case cc misses.
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


class GitSnapshot(TypedDict):
    branch: str
    status: str
    recent_commits: str


# cc caps its own status output at 2000 characters (`oat`,
# chunk-dbb93264.js:69331, applied at :69364); the marker is this hook's own.
STATUS_CAP = 2000
STATUS_TRUNCATED = "\n[status truncated at 2000 characters]"


def git_snapshot(cwd: str) -> GitSnapshot | None:
    """Branch, `status --short` and the last five commits, or None outside a repo.

    cc sends the same facts as its `gitStatus` reminder, but that reminder
    shares one gate with the Bash tool's `# Git` block -- `q7()`,
    chunk-dbb93264.js:69382: `CLAUDE_CODE_DISABLE_GIT_INSTRUCTIONS`, else the
    `includeGitInstructions` setting -- and settings.json turns that gate off
    so `sys_prompt/` is the only git policy the agent receives. A `-p`
    session never carried the reminder at all. This is the copy that survives
    both, and it re-fires with the hook on resume, `/clear` and compact where
    cc's is taken once. The git flags mirror cc's builder (`ADe`,
    chunk-dbb93264.js:69333; the status flags are the `nPo` array at :69332,
    the log call at :69350, and the literal `This is the git status at the
    start of the conversation` at :69369): `--no-optional-locks` so a
    snapshot never takes the index lock from a concurrent session,
    `--ignore-submodules=dirty`,
    five commits, the 2000-character cap. What it leaves out of cc's block:
    `Git user` (claude.sh sets the author through the environment, and the
    config name cc prints is not who the commits are by) and the main-branch
    line (a PR aid; nothing here opens PRs).
    """
    branch = _git(["branch", "--show-current"], cwd)
    if branch is None or branch.returncode != 0:
        return None
    status = _git(
        ["--no-optional-locks", "status", "--short", "--ignore-submodules=dirty"], cwd
    )
    log = _git(["--no-optional-locks", "log", "--oneline", "-n", "5"], cwd)

    def out(result: subprocess.CompletedProcess[str] | None) -> str:
        if result is None or result.returncode != 0:
            return ""
        return result.stdout.rstrip("\n")

    status_text = out(status)
    if len(status_text) > STATUS_CAP:
        status_text = status_text[:STATUS_CAP] + STATUS_TRUNCATED
    return {
        "branch": branch.stdout.strip() or "(detached HEAD)",
        "status": status_text,
        "recent_commits": out(log),
    }
