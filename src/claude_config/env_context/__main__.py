"""SessionStart hook: the dynamic context --system-prompt-file discards.

Claude Code assembles its own `# Environment` and `# Scratchpad Directory`
sections in `sV()` (globals/21.js:13336), and --system-prompt-file replaces
that whole assembly. Everything else the default prompt carries still arrives:
gitStatus is appended to the system prompt, and claudeMd, userEmail and
currentDate come in the system-reminder user message.

Emitting the JSON envelope is not optional. Plain stdout from a SessionStart
hook is injected as `SessionStart hook success: <text>`
(globals/20.js:24499); only hookSpecificOutput.additionalContext is injected
verbatim (globals/20.js:24485). A crash here is safer than it looks: cc
classifies a non-zero hook exit as `non_blocking_error`, which shows stderr
to the *user* but maps to `[]` for the model, so failing loudly tells the
human without polluting the prompt.
"""

from __future__ import annotations

import json
import os
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import cast

from . import drift, environment, render, scratchpad

ROOT = Path(__file__).resolve().parents[3]
MANIFEST = ROOT / "docs" / "env-context-manifest.json"
# One cache for every checkout. Correct only because the key hashes the
# manifest's content rather than its mtime: five worktrees carrying
# byte-identical manifests share a scan instead of invalidating each other.
CACHE = Path.home() / ".claude" / "env-context-drift.json"


def drift_note() -> str | None:
    """A drift note, or None when the pinned field set still matches.

    A failed drift check must not cost the session its env block, so the
    failure becomes a note rather than an exception. It is reported in the
    block itself, not only on stderr: stderr from a hook is not something the
    agent reads, and a check that quietly stopped running is the exact
    failure this hook exists to prevent -- for instance if drift.cached_note
    were ever renamed, this except is what still gets a note into the block
    instead of a silent AttributeError on stderr and nothing in the prompt.
    """
    try:
        return drift.cached_note(drift.find_binary(), MANIFEST, CACHE)
    except Exception as exc:  # noqa: BLE001 - surfaced in the block, not swallowed
        detail = f"{type(exc).__name__}: {exc}"
        print(f"env-context: drift check failed: {detail}", file=sys.stderr)
        script = ROOT / "scripts" / "check-env-context.sh"
        return (
            f"the env-block drift check itself failed ({detail}) and could "
            f"not run; worth mentioning to the user, who can run {script} "
            "to look into it."
        )


def resolved_shell() -> str:
    """The Bash tool's shell, or an explicit statement that none was found.

    `resolve_shell` raises only when no bash or zsh exists anywhere, which is
    the one case where its own message ("Claude Code's Bash tool would fail
    too") is itself the most actionable fact this hook could report. Falling
    back to cc's own bare `unknown` here would be wrong twice: it is the one
    string that means "we did not even look" -- indistinguishable from cc's
    degenerate default -- and it would leave the actionable fact only on
    stderr, which is not something the agent reads, the same reason
    drift_note() surfaces its own failures in the block rather than only
    there.
    """
    try:
        return environment.resolve_shell()
    except RuntimeError as exc:
        print(f"env-context: shell resolution failed: {exc}", file=sys.stderr)
        return "none found — no bash or zsh on this system, so Bash tool calls will fail"


def scratchpad_or_none(
    cwd: str, session_id: str, *, env: Mapping[str, str] | None = None
) -> str | None:
    """The session scratchpad, or None when it could not be created.

    `env` defaults to os.environ, matching the Task 2-6 collaborators this
    function calls (resolve_shell, scratchpad.ensure). Threading it through
    as a parameter rather than reading os.environ directly is what lets the
    background-session gate below be exercised in-process, with an injected
    mapping, instead of only through a subprocess.

    Suppressed entirely in a background session. cc drops its own scratchpad
    section there (`cvi()`, globals/21.js:13624) and names `$CLAUDE_JOB_DIR/tmp`
    instead, so emitting ours would give that session two conflicting
    temp-directory instructions. Hooks come from settings.json and fire
    regardless of which prompt the session runs, so this gate has to live here.

    A cwd whose slug exceeds cc's 200-character limit, a read-only tmp root and
    a `claude-<uid>` owned by another user all raise here. cc survives the
    first of those by appending a hash suffix, so its session keeps working
    while this hook would die for the sake of one missing line. Losing the
    section beats losing the block.
    """
    env = os.environ if env is None else env
    if env.get("CLAUDE_CODE_SESSION_KIND") == "bg":
        return None
    try:
        return str(scratchpad.ensure(env=env, cwd=cwd, session_id=session_id))
    except (OSError, ValueError) as exc:
        print(f"env-context: scratchpad unavailable: {exc}", file=sys.stderr)
        return None


def _require_str(payload: Mapping[str, object], field: str) -> str:
    """cwd and session_id must be str, checked immediately after the parse.

    A missing key or a wrong-typed value means Claude Code's own hook
    payload contract changed -- exactly the drift class this feature exists
    to catch, so it must be loud: SystemExit with a message naming the
    contract, not a KeyError or a TypeError raised incidentally further
    downstream (inside subprocess.run's cwd handling, or scratchpad's path
    building) where nothing at the failure site explains what broke.

    A merely-empty string is a different case: parseable and degenerate,
    not a breach of the contract's shape, so it is left to degrade quietly
    through the existing OSError/ValueError guards in scratchpad_or_none and
    the None-returning git helpers in environment.py.
    """
    if field not in payload:
        raise SystemExit(
            f"SessionStart payload is missing field {field!r}; Claude Code's "
            + "hook contract may have changed"
        )
    value = payload[field]
    if not isinstance(value, str):
        raise SystemExit(
            f"SessionStart payload field {field!r} is {type(value).__name__}, "
            + "expected str; Claude Code's hook contract may have changed"
        )
    return value


def main() -> int:
    # json.loads returns Any; casting here -- rather than leaving the Any to
    # leak into every field below -- is what lets facts: Facts, immediately
    # after, be checked as more than a formality: basedpyright can verify the
    # key set only where the values it is matching against Facts are not
    # themselves Any.
    payload = cast(dict[str, object], json.loads(sys.stdin.read()))
    cwd = _require_str(payload, "cwd")
    session_id = _require_str(payload, "session_id")

    facts: render.Facts = {
        "cwd": cwd,
        "is_git_repo": environment.is_git_repo(cwd),
        "worktree_common_dir": environment.worktree_common_dir(cwd),
        "platform": environment.platform_name(),
        "shell": resolved_shell(),
        "os_version": environment.os_version(),
        "model": cast("str | None", payload.get("model")),
        "session_id": session_id,
        "scratchpad": scratchpad_or_none(cwd, session_id),
        "drift_note": drift_note(),
    }

    json.dump(
        {
            "hookSpecificOutput": {
                "hookEventName": "SessionStart",
                "additionalContext": render.sections(facts),
            }
        },
        sys.stdout,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
