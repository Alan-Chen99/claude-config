"""Assembling the prompt sections from collected facts.

Bullets use the ` - ` prefix Claude Code's own formatter emits (`jSe`,
globals/21.js:13158), so the block reads the same as the one cc produces in
sessions that use its default prompt.
"""

from __future__ import annotations

# cc's own wording, `cTm`, globals/21.js:13688, trimmed to the hazard.
STASH_CAUTION = (
    "The git stash stack is shared with the main checkout and all other worktrees, "
    "and other Claude sessions may push or pop it concurrently. Never use bare "
    "`git stash` / `git stash pop` — you could pop another session's changes. "
    "Prefer a temporary WIP commit to set work aside."
)


def _bullets(items: list[str]) -> str:
    return "\n".join(f" - {item}" for item in items)


def environment_section(facts: dict[str, object]) -> str:
    items: list[str] = [f"Primary working directory: {facts['cwd']}"]

    common_dir = facts.get("worktree_common_dir")
    if common_dir:
        items.append(
            (
                f"This is a git worktree of {common_dir}. Run all commands from this "
                "directory. Do NOT `cd` to the original repository root."
            )
        )
        items.append(STASH_CAUTION)

    items.append(f"Is a git repository: {str(bool(facts['is_git_repo'])).lower()}")
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
        "Use this directory for temporary files instead of `/tmp`:\n"
        f"`{path}`\n\n"
        "It is session-specific, isolated from the project, and is the same "
        "directory your subagents are given."
    )


def sections(facts: dict[str, object]) -> str:
    """The env block, plus the scratchpad section when there is a path to name.

    A scratchpad that could not be created leaves `scratchpad` None. Rendering
    that into the prompt as a path would point the agent at a directory which
    does not exist, so the section is dropped instead — the env block is worth
    having without it.
    """
    blocks = [environment_section(facts)]
    path = facts.get("scratchpad")
    if path:
        blocks.append(scratchpad_section(str(path)))
    return "\n\n".join(blocks)
