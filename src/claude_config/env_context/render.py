"""Assembling the prompt sections from collected facts.

Bullets use the ` - ` prefix Claude Code's own formatter emits (`Rm`,
src/chunk-wgfrtm7w.js:4545), so the bullet formatting matches the block cc
produces in sessions that use its default prompt. The content itself
deliberately diverges from cc's own env block (`sEn`,
src/chunk-wgfrtm7w.js:4662, the `Primary working directory: ` template array
at :4665) in four places: `Shell` reports the shell the Bash tool actually
runs, where cc reports `$SHELL` or the literal `unknown`; `Session ID` has no
cc equivalent; the worktree line names the checkout path, where cc's own
version names none; and the clock line puts an offset and a zone on a date cc
states bare.

The reason once given for that third divergence -- that cc's line describes
only a worktree it created and owns -- stopped being true in 2.1.269, which
sets `isWorktree` from `pP()`, now `Lz()`
(src/chunk-s5xz0z8j.js:1976, in the file whose `git root prime: findGitRoot
already holds a different answer for the start path` warning sits at :1965),
the same common-dir-differs-from-git-dir test
`environment.worktree_common_dir` uses, and so speaks about hand-made
worktrees too. The divergence survives the correction: cc's wording still
names no path.

Since 2.1.269 cc emits its own environment block even under
--system-prompt-file, so this block no longer mirrors it -- it carries only
what cc's does not. Dropped as duplicates on 2026-09-13: the working
directory, the is-a-git-repo flag, the platform, the OS version and the model
line, each of which cc states inside the attachment its `cKe` gate delivers;
and the stash caution, which cc's own worktree block (`OQe`,
src/chunk-wgfrtm7w.js:4552) carries, so the worktree line here names only the
checkout path.

2.1.289 re-derivation: that trim still holds, and cc dropped nothing this
block leans on it for. Two shape changes, neither of which gives a bullet
back. First, `workingDirectory`, `shell` and `osVersion` became optional in
the snapshot schema (`PSe`, src/chunk-wgfrtm7w.js:4558-4568) and each line is
now conditional, with the whole working-directory group -- primary directory,
both worktree lines, the git-repo flag -- omitted together when the directory
is absent and replaced by `YTn` (:4555). The only producer of such a snapshot
is `x8()` (:4635) behind `launchOptions.toolsMachine()`, and nothing in this
build ever calls `replaceToolsMachine` (chunk-zcjzet3s.js:3315), so the
omitting path is unreachable here and the five dropped facts still arrive
unconditionally in practice. Second, cc *added* a bullet this hook has no
counterpart for: a `githubCli` field (`CSe`, :4533) whose text opens
``gh` here is Claude Code's built-in GitHub client`, set only where the agent
proxy arms a `gh` stand-in (chunk-7ek9gdg7.js:2105). Nothing to drop, nothing
to add back.

The scratchpad section stays, and is the one deliberate duplicate. cc's own
scratchpad bullet and cc's own `mkdir` of that directory sit behind the same
server-resolved gate -- `Xw()` (`src/chunk-8wf3pk41.js:8038`) is
`tengu_scratch` or `isArtifactToolEligible()`, and `oEn()`
(`src/chunk-wgfrtm7w.js:4655`) returns early without it -- so cc's bullet can
disappear with no change to the binary, which is the one thing
`scripts/check-env-context.sh` watches. A gate flip would otherwise leave the
session with no scratchpad instruction at all.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import NotRequired, TypedDict

from .environment import GitSnapshot

class Resumption(TypedDict):
    """What the resumption block is built from.

    `skill_body` is skills/resume-from-summary/SKILL.md without its
    frontmatter (`skill_body()`); `target` is what its `cc-pretty` command
    skeletons -- the transcript path from the SessionStart payload, or the
    session id when the payload carries none, which cc-pretty resolves too.
    """

    skill_body: str
    target: str


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
    clock: str
    shell: str
    session_id: str
    worktree_common_dir: NotRequired[str | None]
    scratchpad: NotRequired[str | None]
    drift_note: NotRequired[str | None]
    git_snapshot: NotRequired[GitSnapshot | None]
    resumption: NotRequired[Resumption | None]


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

    # cc states the date and nothing else about the clock: `currentDate` is a
    # bare `Today's date is YYYY-MM-DD.` built from local-time getters
    # (`Lqr()`, chunk-329679e2.js:39, reached from `currentDate` at
    # chunk-wgfrtm7w.js:30108), and no offset, zone or time of day accompanies
    # it anywhere in the context. 2.1.289 adds a zone-aware branch ahead of
    # those getters, but the session store it reads has no writer anywhere in
    # the binary, so the date is still the process's local one. A local date
    # alone does not say which day it is in UTC -- west of Greenwich the two
    # differ for the last hours of every evening -- so the offset is the fact
    # that makes cc's line readable, and the zone name is what makes the next
    # transition predictable.
    items.append(
        (
            f"Clock at session start: {facts['clock']}. Claude Code's "
            "`Today's date is` line is a local date in this zone carrying no "
            "zone or offset of its own, so it is not the UTC date whenever the "
            "two differ; `date -Iseconds` and `date -u` are authoritative for "
            "the current time."
        )
    )

    # Labelled, not `Shell:`, because cc's block carries a `Shell:` line of its
    # own reporting a different quantity -- measured in a live session on
    # 2026-09-13, cc said `unknown` where this says `/bin/bash`. Two bullets
    # spelled the same way and disagreeing is worse than either alone. Since
    # 2.1.289 cc's line is conditional, so a snapshot without a shell would
    # leave this one unopposed rather than contradicted -- the distinct label
    # costs nothing there and still earns its keep everywhere else.
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


def skill_body(text: str) -> str:
    """A SKILL.md minus its YAML frontmatter, stripped."""
    match = re.match(r"\A---\n.*?\n---\n", text, re.DOTALL)
    return (text[match.end():] if match else text).strip()


# The one line of SKILL.md the hook renders away: it defines `<target>` for a
# reader who invokes the skill by hand, and the hook has already filled it in.
TARGET_DEFINITION = "`<target>`:"


def resumption_section(res: Resumption, scratchpad: str | None) -> str:
    """The resume-from-summary skill's body, placeholders filled, delivered
    with the first post-boundary message rather than named from the prompt's
    tail: the summary's closing "Resume directly" is the most recent order the
    model meets, in the user turn, and a system-prompt line far from it loses
    to it (skills/resume-from-summary/README.md, Sonnet measurements). This
    section meets the model where that order does.

    The body itself, not a directive to invoke the skill: its opening rules
    govern how the summary is read, so they have to be in context before the
    first post-boundary thinking, which a `Skill` call cannot guarantee --
    under the prompt line alone Opus at effort `max` reasoned 13-16k tokens on
    the summary before calling. One source serves both deliveries: this hook
    after a compaction, the `Skill` tool for a handoff typed into a fresh
    session, where no SessionStart payload says `compact`.

    `<scratchpad>` stays literal when the scratchpad could not be created --
    the same text the `Skill` tool delivers, so the model picks a directory as
    it would there, rather than being sent to a path that does not exist.
    """
    kept = [
        line for line in res["skill_body"].split("\n") if not line.startswith(TARGET_DEFINITION)
    ]
    body = re.sub(r"\n{3,}", "\n\n", "\n".join(kept)).strip().replace("<target>", res["target"])
    if scratchpad:
        body = body.replace("<scratchpad>", scratchpad)
    # Stated as a fact, not left to the model's reading: the hook fires only
    # when cc's payload says the turn opens on a summary, and the one Sonnet run
    # under a wording that merely named the state read the context as "a fresh
    # conversation rather than a true resumed session" and skipped the skill.
    return (
        "# Continuing from a compaction summary\n\n"
        "This context opens on a compaction summary of this same session, so "
        "the `resume-from-summary` skill below applies; it is delivered here, "
        "and no `Skill` call is needed. Run its two commands before anything "
        "else — before reasoning about what the summary says and before any "
        "other tool call, `pre_output.record` included; the summary's closing "
        "\"Resume directly\" governs your reply, not this, and does not waive it."
        f"\n\n{body}"
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
    res = facts.get("resumption")
    if res:
        blocks.insert(0, resumption_section(res, path))
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
