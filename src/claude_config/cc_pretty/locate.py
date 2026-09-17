"""Turn a cc-pretty argument into the transcript it names.

An argument is either a path or an id. A reader almost always has the id: it is
what a session start reports, what a record's `sessionId` or `agentId` field
holds, what a notification names. Turning one into a path by hand means knowing
the project-slug encoding and running a find.
"""

from __future__ import annotations

import glob
import os
from dataclasses import dataclass

_SUFFIX = ".jsonl"
_MAX_LISTED = 10


class SessionNotFound(Exception):
    """No transcript matches an id, or more than one does."""


@dataclass(frozen=True)
class Located:
    """Where a cc-pretty argument resolved to.

    ``source_id`` carries the id when the argument was resolved by search, and is
    None when it named a file directly. The render announces the resolution only
    in the first case, where the reader cannot otherwise tell which file was read.
    """

    path: str
    source_id: str | None


def _config_root(explicit: str | None) -> str:
    """The directory Claude Code itself reads."""
    chosen = explicit or os.environ.get("CLAUDE_CONFIG_DIR") or "~/.claude"
    return os.path.expanduser(chosen)


def _candidates(config_root: str) -> list[str]:
    """Every transcript under ``config_root``, session and subagent alike."""
    projects = os.path.join(config_root, "projects")
    # The recursive wildcard is load-bearing: Workflow-tool subagents sit one
    # level deeper, under subagents/workflows/wf_<id>/. So is the agent- stem,
    # which excludes that same directory's journal.jsonl — a record file that
    # shares the extension without being a transcript.
    return glob.glob(os.path.join(projects, "*", f"*{_SUFFIX}")) + glob.glob(
        os.path.join(projects, "*", "*", "subagents", "**", f"agent-*{_SUFFIX}"),
        recursive=True,
    )


def _matching(arg: str, paths: list[str]) -> list[str]:
    # Both spellings of a subagent id occur in the logs: the agentId field holds
    # bare hex, while filenames and inline references carry the agent- prefix.
    prefixes = (arg, f"agent-{arg}")
    return sorted(
        os.path.abspath(p)
        for p in paths
        if os.path.basename(p)[: -len(_SUFFIX)].startswith(prefixes)
    )


def resolve_log_arg(arg: str, *, config_dir: str | None = None) -> Located:
    """Resolve ``arg`` to exactly one transcript.

    An existing file is never reinterpreted, so a file named like an id opens as
    itself. Anything else is searched for by stem prefix across both transcript
    families under ``<config dir>/projects``.
    """
    expanded = os.path.expanduser(arg)
    if os.path.isfile(expanded):
        return Located(path=os.path.abspath(expanded), source_id=None)

    root = _config_root(config_dir)
    found = _matching(arg, _candidates(root))
    if len(found) == 1:
        return Located(path=found[0], source_id=arg)

    if not found:
        # Naming the directory matters: the common cause is a transcript logged
        # under a different CLAUDE_CONFIG_DIR, which the argument cannot reveal.
        raise SessionNotFound(
            f"no transcript matches {arg!r}, and no such file — "
            f"searched {os.path.join(root, 'projects')}"
        )

    listed = "\n  ".join(found[:_MAX_LISTED])
    remainder = len(found) - _MAX_LISTED
    more = f"\n  ... and {remainder} more" if remainder > 0 else ""
    raise SessionNotFound(
        f"{arg!r} matches {len(found)} transcripts:\n  {listed}{more}"
    )
