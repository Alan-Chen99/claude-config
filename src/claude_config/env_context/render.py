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

2.1.269 also moved the scratchpad from a section of its own into a bullet of
this block, and the model and knowledge-cutoff lines out of it entirely, so
this rendering no longer mirrors cc's shape. It is left as it is pending the
larger question `__main__`'s docstring records: cc now emits this block
itself even under --system-prompt-file, so most of what is rendered here is
a second copy.
"""

from __future__ import annotations

from pathlib import Path
from typing import NotRequired, TypedDict

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
    platform: str
    shell: str
    os_version: str
    session_id: str
    worktree_common_dir: NotRequired[str | None]
    model: NotRequired[str | None]
    scratchpad: NotRequired[str | None]
    drift_note: NotRequired[str | None]


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
    items: list[str] = [f"Primary working directory: {facts['cwd']}"]

    common_dir = facts.get("worktree_common_dir")
    if common_dir:
        main_checkout = _main_checkout(common_dir)
        items.append(
            (
                f"This is a git worktree of {main_checkout}. Run all commands "
                "from this directory and make changes only here; reading "
                f"{main_checkout} is fine, but do not edit, commit, or build "
                "there."
            )
        )
        items.append(STASH_CAUTION)

    items.append(f"Is a git repository: {str(facts['is_git_repo']).lower()}")
    items.append(f"Platform: {facts['platform']}")
    items.append(f"Shell: {facts['shell']}")
    items.append(f"OS Version: {facts['os_version']}")

    model = facts.get("model")
    if model:
        items.append(f"You are powered by the model {model}")

    items.append(f"Session ID: {facts['session_id']}")

    note = facts.get("drift_note")
    if note:
        items.append(f"NOTE: {note}")

    header = "# Environment\nYou have been invoked in the following environment: "
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


def sections(facts: Facts) -> str:
    """The env block, plus the scratchpad section when there is a path to name.

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
    return "\n\n".join(blocks)
