"""pre_output.record -- the pre-output rule reminder, and the turn's summary.

Two jobs, in this order of importance.

The reminder is why the command exists. Asking the model to externalize its
state into a tool call creates a breakpoint at which the rules below re-enter
its context at generation time; the argument's content matters less than the
act of composing it. The reminder therefore prints even when the second job
fails.

The record is read by `claude_config.ntfy_hook`, so the "Done" push carries
the session's own summary instead of a second model's guess at the transcript.
`ntfy_hook.do_cancel` unlinks the file on UserPromptSubmit, which is what makes
a file that exists mean "written during the turn that is now ending".
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

RULES = """\
<system-reminder>
IMPORTANT RULES:
- NEVER ask user to read files or run commands that you have not already read or run yourself
</system-reminder>"""


def record_path(session_id: str) -> Path:
    """Where a session's pre-output record lives.

    Beside `/tmp/claude-ntfy-<session>.{pid,done}`, which `ntfy_hook` keys the
    same way. This is the only definition of the path; `ntfy_hook` imports it.
    """
    return Path(f"/tmp/claude-pre-output-{session_id}.json")


def _write(session_id: str, payload: dict) -> None:
    """Replace the session's record atomically.

    The Stop hook reads this file at a moment this process does not control,
    so a half-written file must never be visible under the final name.
    """
    dest = record_path(session_id)
    fd, tmp = tempfile.mkstemp(dir=str(dest.parent), prefix=f"{dest.name}.", suffix=".tmp")
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        json.dump(payload, handle)
    os.replace(tmp, dest)


def _record(argv: list[str]) -> str | None:
    """Write the turn's record. Returns None on success, else why not."""
    session_id = os.environ.get("CLAUDE_CODE_SESSION_ID", "").strip()
    if not session_id:
        return (
            "CLAUDE_CODE_SESSION_ID is not set, so the record has no session to "
            "belong to and the ntfy \"Done\" push falls back to a generated "
            "summary. Claude Code exports this variable into every shell it "
            "runs, and agent-tools scopes its run state by it too, so seeing "
            "this from inside a Bash tool call means both are affected."
        )

    if len(argv) != 1:
        return (
            f"expected exactly one JSON argument, got {len(argv)}. The shell "
            "split the argument, which single quotes around the JSON do not "
            "survive when the JSON itself contains an apostrophe; a heredoc "
            "into a file and \"$(cat file)\" does survive it."
        )

    try:
        payload = json.loads(argv[0])
    except json.JSONDecodeError as exc:
        return f"argument is not valid JSON: {exc}"

    if not isinstance(payload, dict):
        return f"argument is a JSON {type(payload).__name__}, expected an object"

    summary = payload.get("summary")
    if not isinstance(summary, str) or not summary.strip():
        return 'no non-empty "summary" field, which is the field the ntfy push sends'

    _write(session_id, payload)
    return None


def main(argv: list[str] | None = None) -> int:
    problem = _record(sys.argv[1:] if argv is None else argv)

    if problem is None:
        print("recorded successfully.\n")
    else:
        # stdout never claims a write that did not happen; the reminder still
        # lands, because it is the half of this command that carries the value.
        print(f"pre_output.record: NOT recorded -- {problem}", file=sys.stderr)

    print(RULES)
    return 0 if problem is None else 1


if __name__ == "__main__":
    sys.exit(main())
