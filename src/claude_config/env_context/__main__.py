"""SessionStart hook: the dynamic context --system-prompt-file discards.

Claude Code assembles its own `# Environment` and `# Scratchpad Directory`
sections in `sV()` (globals/21.js:13336), and --system-prompt-file replaces
that whole assembly. Everything else the default prompt carries still arrives:
gitStatus is appended to the system prompt, and claudeMd, userEmail and
currentDate come in the system-reminder user message.

Emitting the JSON envelope is not optional. Plain stdout from a SessionStart
hook is injected as `SessionStart hook success: <text>`
(globals/20.js:24499); only hookSpecificOutput.additionalContext is injected
verbatim (globals/20.js:24485).
"""

from __future__ import annotations

import json
import os
import sys
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
    agent reads, and a check that quietly stopped running is the exact failure
    this hook exists to prevent.
    """
    try:
        return drift.cached_note(drift.find_binary(), MANIFEST, CACHE)
    except Exception as exc:  # noqa: BLE001 - surfaced in the block, not swallowed
        print(f"env-context: drift check failed: {exc}", file=sys.stderr)
        return f"env-block drift check failed ({exc}). Run scripts/check-env-context.sh."


def resolved_shell() -> str:
    """The Bash tool's shell, or cc's own literal `unknown`.

    `resolve_shell` raises when no bash or zsh exists, which is the honest
    answer for a function whose job is to name one. It is the wrong answer for
    this hook: an exception here costs the session its whole env block, and
    the block is still worth having without the shell line. `unknown` is what
    cc itself prints in that position (`Kml()`, globals/21.js:13560).
    """
    try:
        return environment.resolve_shell()
    except RuntimeError as exc:
        print(f"env-context: shell resolution failed: {exc}", file=sys.stderr)
        return "unknown"


def scratchpad_or_none(cwd: str, session_id: str) -> str | None:
    """The session scratchpad, or None when it could not be created.

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
    if os.environ.get("CLAUDE_CODE_SESSION_KIND") == "bg":
        return None
    try:
        return str(scratchpad.ensure(cwd=cwd, session_id=session_id))
    except (OSError, ValueError) as exc:
        print(f"env-context: scratchpad unavailable: {exc}", file=sys.stderr)
        return None


def main() -> int:
    # json.loads returns Any; casting here -- rather than leaving the Any to
    # leak into every field below -- is what lets facts: Facts, immediately
    # after, be checked as more than a formality: basedpyright can verify the
    # key set only where the values it is matching against Facts are not
    # themselves Any.
    payload = cast(dict[str, object], json.loads(sys.stdin.read()))
    cwd = cast(str, payload["cwd"])
    session_id = cast(str, payload["session_id"])

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
