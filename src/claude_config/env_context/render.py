"""Assembling the prompt sections from collected facts.

Bullets use the ` - ` prefix Claude Code's own formatter emits (`RT`,
chunk-dbb93264.js:29113), so the bullet formatting matches the block cc
produces in sessions that use its default prompt. The content itself
deliberately diverges from cc's own env block (`AWr`,
chunk-dbb93264.js:29195) in three places: `Shell` reports the shell the Bash
tool actually runs, where cc reports `$SHELL` or the literal `unknown`;
`Session ID` has no cc equivalent; and the worktree line names the checkout
path, where cc's own version names none.

The reason once given for that third divergence -- that cc's line describes
only a worktree it created and owns -- stopped being true in 2.1.269, which
sets `isWorktree` from `pP()` (chunk-arxpc433.js:1653), the same
common-dir-differs-from-git-dir test `environment.worktree_common_dir` uses,
and so speaks about hand-made worktrees too. The divergence survives the
correction: cc's wording still names no path.

Since 2.1.269 cc emits its own environment block even under
--system-prompt-file, so this block no longer mirrors it -- it carries only
what cc's does not. Dropped as duplicates on 2026-09-13: the working
directory, the is-a-git-repo flag, the platform, the OS version and the model
line, each of which cc states unconditionally inside the attachment its
`p$t` gate delivers.

The scratchpad section stays, and is the one deliberate duplicate. cc's own
scratchpad bullet and cc's own `mkdir` of that directory sit behind the same
server-resolved gate -- `NA()` (`src/chunk-tnzzwz8r.js:13367`) is
`tengu_scratch` or `isArtifactToolEligible()`, and `CWr()`
(`src/chunk-dbb93264.js:29188`) returns early without it -- so cc's bullet can
disappear with no change to the binary, which is the one thing
`scripts/check-env-context.sh` watches. A gate flip would otherwise leave the
session with no scratchpad instruction at all.
"""

from __future__ import annotations

from pathlib import Path
from typing import NotRequired, TypedDict

from .environment import GitSnapshot

# cc's own wording, `KUt`, chunk-dbb93264.js:29119, in full. Pinned by
# `scripts/check-prompt-upstream.py`, which is what fails when cc rewords it:
# `scripts/check-env-context.sh` pins only the first 182 characters, and the
# clause that matters is past that. The second half
# defines what "bare" means by naming the safe alternative (a tagged,
# recoverable stash) — drop it and "never use bare `git stash`" has no
# working definition of non-bare, and the obvious misreading (bare means no
# arguments) reaches for `git stash push -m wip` then `git stash apply
# stash@{0}`, exactly the index race this clause exists to prevent.
STASH_CAUTION = (
    "The git stash stack is shared with the main checkout and all other worktrees, "
    "and other Claude sessions may push or pop it concurrently. Never use bare "
    "`git stash` / `git stash pop` — you could pop another session's changes. "
    "Prefer a temporary WIP commit to set work aside; if you must stash, use "
    "`git stash push -u -m \"<unique-tag>\"`, immediately capture your entry's "
    "SHA via `git stash list --format='%H %gs'`, restore with `git stash apply "
    "<sha>` (not pop), and afterwards drop the entry, re-finding its current "
    "`stash@{n}` by tag first."
)


class Facts(TypedDict):
    """The facts dict environment_section()/sections() consume.

    Required keys are always supplied by the orchestrator (Task 7); the
    optional ones are genuinely nullable states — no worktree, no model
    reported, an uncreatable scratchpad, no drift — not values that happen
    to be missing by omission. basedpyright checks this shape wherever a
    Facts value is constructed. It cannot check value types coming from
    json.loads, which are Any regardless of this declaration; the win here
    is the key set and the required/optional split, the half of the
    contract that actually rots as keys are added.
    """

    cwd: str
    is_git_repo: bool
    shell: str
    session_id: str
    worktree_common_dir: NotRequired[str | None]
    scratchpad: NotRequired[str | None]
    drift_note: NotRequired[str | None]
    git_snapshot: NotRequired[GitSnapshot | None]


def _bullets(items: list[str]) -> str:
    return "\n".join(f" - {item}" for item in items)


def _main_checkout(common_dir: str) -> str:
    """The checkout directory a worktree line should name.

    `worktree_common_dir()` returns git's --git-common-dir, which for an
    ordinary (non-bare) main checkout is `<main>/.git` — naming that .git
    directory as the worktree's origin, then telling the agent not to `cd`
    to "the original repository root", names one path and refers to
    another it never gave. A bare main has no `.git` path *component* —
    its common-dir is the checkout itself, e.g. `/repos/bare-repo.git` —
    so stripping is gated on the last path component being exactly ".git",
    not merely on the string ending in those four characters. Path.parent
    and Path.name are pure string manipulation; nothing here touches the
    filesystem.
    """
    path = Path(common_dir)
    return str(path.parent) if path.name == ".git" else common_dir


def environment_section(facts: Facts) -> str:
    items: list[str] = []

    common_dir = facts.get("worktree_common_dir")
    if common_dir:
        main_checkout = _main_checkout(common_dir)
        items.append(
            (
                f"The checkout this worktree belongs to is {main_checkout}: "
                "reading it is fine, but do not edit, commit, or build there."
            )
        )
        items.append(STASH_CAUTION)

    # Labelled, not `Shell:`, because cc's block carries a `Shell:` line of its
    # own reporting a different quantity -- measured in a live session on
    # 2026-09-13, cc said `unknown` where this says `/bin/bash`. Two bullets
    # spelled the same way and disagreeing is worse than either alone.
    items.append(f"Shell the Bash tool runs: {facts['shell']}")
    items.append(f"Session ID: {facts['session_id']}")

    note = facts.get("drift_note")
    if note:
        items.append(f"NOTE: {note}")

    # Not cc's own preamble, which this block used to borrow verbatim: it no
    # longer mirrors cc's block, and two identically-headed `# Environment`
    # sections in one context read as a contradiction rather than an addition.
    header = (
        "# Environment (supplement)\n"
        "Facts and rules Claude Code's own environment block does not carry:"
    )
    return f"{header}\n{_bullets(items)}"


def scratchpad_section(path: str) -> str:
    return (
        "# Scratchpad Directory\n\n"
        "Use this directory for temporary files instead of `/tmp` or other "
        "system temp directories:\n"
        f"`{path}`\n\n"
        "Only use `/tmp` if the user explicitly requests it.\n\n"
        "It is session-specific, isolated from the project, and is normally "
        "the same directory your subagents are given."
    )


def git_status_section(snap: GitSnapshot) -> str:
    """cc's gitStatus reminder minus its preamble: the header says when the
    snapshot was taken, which is all the preamble said."""
    return (
        "# Git status at session start\n"
        f"Current branch: {snap['branch']}\n\n"
        f"Status:\n{snap['status'] or '(clean)'}\n\n"
        f"Recent commits:\n{snap['recent_commits'] or '(none)'}"
    )


def sections(facts: Facts) -> str:
    """The supplement block, plus the scratchpad section when there is a path.

    A scratchpad that could not be created leaves `scratchpad` None. Rendering
    that into the prompt as a path would point the agent at a directory which
    does not exist, so the section is dropped instead — the env block is worth
    having without it.
    """
    blocks = [environment_section(facts)]
    path = facts.get("scratchpad")
    if path:
        # facts["scratchpad"] is already str (Facts declares it str | None,
        # and scratchpad_or_none() is its only producer) -- str() here would
        # just re-wrap a str in str(), which scratchpad_or_none already did
        # to convert scratchpad.ensure()'s Path into the str this dict needs.
        blocks.append(scratchpad_section(path))
    snap = facts.get("git_snapshot")
    if snap:
        blocks.append(git_status_section(snap))
    return "\n\n".join(blocks)
