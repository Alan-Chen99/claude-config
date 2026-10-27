"""Turn an id into the transcript it names.

Two callers: a cc-pretty argument, which is a path or an id, and a rendered
subagent call, whose result names only the id of the agent it spawned. A reader
almost always has the id: it is what a session start reports, what a record's
`sessionId` or `agentId` field holds, what a notification names. Turning one
into a path by hand means knowing the project-slug encoding and running a find.
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


def config_root(explicit: str | None) -> str:
    """The directory Claude Code itself reads."""
    chosen = explicit or os.environ.get("CLAUDE_CONFIG_DIR") or "~/.claude"
    return os.path.expanduser(chosen)


def _subagent_transcripts(tree: str) -> list[str]:
    """Every subagent transcript under ``tree`` (a glob pattern too)."""
    # The recursive wildcard is load-bearing: Workflow-tool subagents sit one
    # level deeper, under subagents/workflows/wf_<id>/. So is the agent- stem,
    # which excludes that same directory's journal.jsonl — a record file that
    # shares the extension without being a transcript.
    return glob.glob(
        os.path.join(tree, "subagents", "**", f"agent-*{_SUFFIX}"),
        recursive=True,
    )


def _candidates(root: str) -> list[str]:
    """Every transcript under ``root``, session and subagent alike."""
    projects = os.path.join(root, "projects")
    return glob.glob(os.path.join(projects, "*", f"*{_SUFFIX}")) + (
        _subagent_transcripts(os.path.join(projects, "*", "*"))
    )


def session_tree(log_path: str) -> str:
    """The directory whose ``subagents/`` holds the agents ``log_path``'s session spawned.

    A session's is the directory named for its transcript, beside it. A
    subagent's own transcript sits inside that tree — nested agents are written
    flat into the same ``subagents/``, a workflow's agents one level further
    down — so the tree is everything above the last ``subagents`` component.
    """
    parts = log_path.split(os.sep)
    if "subagents" in parts[:-1]:
        cut = len(parts) - 1 - parts[::-1].index("subagents")
        return os.sep.join(parts[:cut])
    return log_path.removesuffix(_SUFFIX)


def subagent_index(
    log_path: str | None, *, config_dir: str | None = None
) -> dict[str, list[str]]:
    """Agent id → its transcript path(s), as seen from a render of ``log_path``.

    The log's own session tree answers first and alone: it is where every agent
    the session spawned is written, and it is the only place a log copied out of
    the config dir has its agents. The rest of ``<config dir>/projects`` answers
    for an id the tree lacks. That is the resumed session: its records are copied
    in under the new session id, while the agents they name stay in the tree of
    the session that spawned them. More than one path is listed rather than
    guessed between.

    ``log_path`` None, or a non-file source such as an intercept capture, has no
    tree of its own and is answered from the config dir alone.
    """
    def stem_id(path: str) -> str:
        return os.path.basename(path)[len("agent-"): -len(_SUFFIX)]

    own: dict[str, list[str]] = {}
    if log_path and os.path.isfile(log_path):
        for path in _subagent_transcripts(glob.escape(session_tree(log_path))):
            own.setdefault(stem_id(path), []).append(os.path.abspath(path))

    elsewhere: dict[str, list[str]] = {}
    projects = os.path.join(config_root(config_dir), "projects")
    for path in _subagent_transcripts(os.path.join(projects, "*", "*")):
        elsewhere.setdefault(stem_id(path), []).append(os.path.abspath(path))

    return {**{k: sorted(v) for k, v in elsewhere.items()},
            **{k: sorted(v) for k, v in own.items()}}


def workflow_transcripts(transcript_dir: str) -> list[str] | None:
    """The agent transcripts a Workflow run wrote, or None when its directory is gone."""
    if not os.path.isdir(transcript_dir):
        return None
    return sorted(glob.glob(os.path.join(glob.escape(transcript_dir), f"agent-*{_SUFFIX}")))


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

    root = config_root(config_dir)
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
