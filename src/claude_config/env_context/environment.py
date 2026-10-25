"""Machine facts for the env block.

Claude Code's own env block reports `$SHELL`, falling back to the literal
string `unknown` (`uao()`, chunk-j0tbz6ra.js:3450, whose win32 arm now reads
`PowerShell (primary); ${vGn}.` from the fragment at :3405). That is not the
shell it runs commands with: the Bash tool resolves one independently
(`yyi()`, chunk-j0tbz6ra.js:126874, which logs
`is not a valid bash/zsh path, falling back to detection`) and exports it.
`resolve_shell` mirrors the Bash tool, so the reported shell is the one Bash
tool commands execute under.
"""

from __future__ import annotations

import re
import sys

import os
import shutil
import subprocess
from collections.abc import Callable, Mapping, Sequence
from datetime import datetime
from pathlib import Path
from typing import TypedDict

SEARCH_DIRS: tuple[str, ...] = ("/bin", "/usr/bin", "/usr/local/bin", "/opt/homebrew/bin")

ZONEINFO = Path("/usr/share/zoneinfo")


def _zone_name(candidate: str) -> str | None:
    """`candidate` if it names a zone under ZONEINFO, else None.

    The file check is what separates a zone name from a string that merely
    looks like one, and the two syntactic rejections carry their own weight:
    `/UTC` is what apt's tzdata postinst writes into /etc/timezone when
    debconf has nothing to answer from, and it resolves to a real file
    (`ZONEINFO//UTC`) while naming nothing `ZoneInfo()` or another host can
    look up. `..` is rejected for the same reason — a path that resolves is
    not a name.
    """
    name = candidate.strip()
    if not name or name.startswith("/") or ".." in name:
        return None
    return name if (ZONEINFO / name).is_file() else None


def _read(path: Path) -> str | None:
    """File contents, or None when the file is absent or unreadable.

    A probe, not a suppressed error: every caller below is asking whether a
    given machine states its timezone, and "it does not" is one of the
    answers, indistinguishable in effect from a directory that cannot be read.
    """
    try:
        return path.read_text()
    except OSError:
        return None


def local_zone_name(
    env: Mapping[str, str] | None = None, etc: Path | None = None
) -> str | None:
    """The IANA name of the local zone, or None when nothing states one.

    No stdlib call answers this. A tzfile carries offsets and abbreviations
    but not its own name, which is why the name has to be recovered from
    whichever of three places wrote it, consulted in the order the C library
    resolves them: TZ, which glibc reads ahead of both files and which
    `docker-compose.yml` sets for every personal-env container; then
    /etc/timezone, which Debian and Ubuntu hosts write; then the
    ZONEINFO-relative target of the /etc/localtime symlink, all that is left
    on a host with no /etc/timezone at all.

    Three candidates rather than one because this hook runs on the host and
    inside the container, and those two machines state it differently. `etc`
    is where the two files are looked for, the same injection `resolve_shell`
    takes for its search dirs, and for the same reason: the fallbacks are two
    thirds of the behaviour and are otherwise reachable only on a machine
    configured to exercise them.

    A corrupted zoneinfo tree is out of reach here and deliberately so. Where
    a bind mount has replaced the file ZONEINFO/Etc/UTC with another zone's,
    every reading inside that container agrees with every other -- the name,
    the offset, the abbreviation and `ZoneInfo()` all come from the swapped
    bytes -- so no comparison made here can see it. The fix is to not mount
    that way; `docker-compose.yml` carries why.
    """
    env = os.environ if env is None else env
    etc = Path("/etc") if etc is None else etc

    if name := _zone_name(env.get("TZ", "")):
        return name
    if (written := _read(etc / "timezone")) and (name := _zone_name(written)):
        return name
    try:
        target = (etc / "localtime").readlink()
    except OSError:
        return None
    try:
        return _zone_name(str(target.relative_to(ZONEINFO)))
    except ValueError:
        return None


def clock_line() -> str:
    """Local time now, with its offset and whatever names its zone.

    `astimezone()` on a naive now attaches the zone the C library resolved, so
    the offset and the abbreviation are always available and always agree with
    what `date` prints in the same shell. The IANA name is not always
    available, and an unavailable one is omitted rather than guessed: DST
    arithmetic turns on the name, so a wrong one is worse than none.

    No `env` parameter, unlike its collaborators: the offset comes from the
    process's own clock and only `tzset()` moves it, so an injected mapping
    could name one zone while the offset beside it came from another. A test
    that wants a different zone sets TZ and calls `time.tzset()`, which is
    what the process does when compose hands it one.
    """
    now = datetime.now().astimezone()
    zone = local_zone_name()
    named = ", ".join(part for part in (zone, now.tzname()) if part)
    stamp = now.isoformat(timespec="seconds")
    return f"{stamp} ({named})" if named else stamp


def _executable(path: str) -> bool:
    """Whether `path` names something runnable, mirroring `kot()`,
    chunk-j0tbz6ra.js:126860 -- an `X_OK` access check, then the candidate run
    with `["--version"]` under `timeout: 1000`.

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
    """Return the shell the Bash tool will run, mirroring `yyi()`,
    chunk-j0tbz6ra.js:126874 (search dirs
    `["/bin", "/usr/bin", "/usr/local/bin", "/opt/homebrew/bin"]` at :126881).

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
    `pP()`, now `Sq()` (chunk-dc0nzty2.js:2846) -- git root's `.git` is a
    `gitdir:` pointer whose `commondir` resolves elsewhere (`Et()`, :2757,
    reached through `oi()`, :2798), which is the same question this asks of
    git -- so the two agree on which directories count, and this no longer
    covers a case cc misses.
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


# cc caps its own status output at 2000 characters (`RYe`,
# chunk-j0tbz6ra.js:55250, applied at :55318 with the message
# `... (truncated because it exceeds 2k characters`); the marker is this
# hook's own.
STATUS_CAP = 2000
STATUS_TRUNCATED = "\n[status truncated at 2000 characters]"


def git_snapshot(cwd: str) -> GitSnapshot | None:
    """Branch, `status --short` and the last five commits, or None outside a repo.

    cc sends the same facts as its `gitStatus` reminder, but that reminder
    shares one gate with the Bash tool's `# Git` block -- `Xpt()`,
    chunk-j0tbz6ra.js:55336: `CLAUDE_CODE_DISABLE_GIT_INSTRUCTIONS`, else the
    `includeGitInstructions` setting -- and settings.json turns that gate off
    so `sys_prompt/` is the only git policy the agent receives. A `-p`
    session never carried the reminder at all. This is the copy that survives
    both, and it re-fires with the hook on resume, `/clear` and compact where
    cc's is taken once. The git flags mirror cc's builder (`ZGn`,
    chunk-j0tbz6ra.js:55255; the status flags are the `jKo` array at :55251,
    the log call at :55308, and the literal `This is the git status at the
    start of the conversation` at :55323): `--no-optional-locks` so a
    snapshot never takes the index lock from a concurrent session,
    `--ignore-submodules=dirty`,
    five commits, the 2000-character cap. What it leaves out of cc's block:
    `Git user` (claude.sh sets the author through the environment, and the
    config name cc prints is not who the commits are by) and the main-branch
    line (a PR aid; nothing here opens PRs).

    cc's own copy is a `session_context` attachment field, never part of the
    `# Environment` block (the field list `gan` is
    `["userEmail", "attachedProject", "gitStatus", "perforceMode"]`,
    chunk-j0tbz6ra.js:3885). 2.1.281 moved the git reads off the first frame,
    which only changed *when* they run: the prefetch (`pWe`, :55376) warms a
    promise the prompt-context build awaits (chunk-tqjdehqd.js:1625), so the
    section still rides the first request wherever `vRo()` (chunk-j0tbz6ra.js:55368,
    `!CLAUDE_CODE_REMOTE && Xpt()`) allows it -- which here it does not.
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


_COMPACT_BOUNDARY = re.compile(r'"subtype"\s*:\s*"compact_boundary"')


def continues_from_summary(source: object, transcript_path: object, skill_file: Path) -> bool:
    """Whether the session's next turn opens on a compaction summary.

    cc's SessionStart payload names its trigger in `source`: `compact` is the
    turn right after a compaction; `resume` reopens a transcript that may or
    may not hold one, so the file decides -- a `compact_boundary` record is
    written only by compaction and survives every later turn. `startup` and
    `clear` open on no summary. The directive is dropped when the skill it
    names is not installed beside this hook, so no session is told to invoke
    a name the Skill tool cannot resolve.
    """
    if not skill_file.is_file():
        return False
    if source == "compact":
        return True
    if source != "resume" or not isinstance(transcript_path, str):
        return False
    try:
        with open(transcript_path, encoding="utf-8", errors="replace") as fh:
            return any(_COMPACT_BOUNDARY.search(line) for line in fh)
    except OSError as exc:
        print(f"env-context: transcript unreadable, no resumption section: {exc}", file=sys.stderr)
        return False
