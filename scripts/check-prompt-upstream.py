#!/usr/bin/env python3
"""Check the prompt text this repo borrows from Claude Code against the installed
build.

Two files author prompt text by copying Claude Code's. `--system-prompt-file`
replaces every system-prompt block but the one-line identity block, so
`sys_prompt/alan-default-next.md` supplies the whole prompt; and the SessionStart
hook in `src/claude_config/env_context/` renders an environment block of its own.
Since 2.1.269 that block sits beside the copy Claude Code delivers through
`messages[]` rather than standing in for a discarded one — `env_context/__main__.py`
holds that finding. Both files carry passages lifted from upstream, whose own copy
is their only source of truth — and upstream rewords prose between releases. That
is what this script pins, and the pin holds either way: a borrowed sentence goes
stale whether the block around it is the only copy or the second one.

`scripts/check-env-context.sh` covers the env block's *field set* against the
installed binary. It does not cover the wording: it pins the stash caution as a
182-character prefix of a 540-character copy, and the clause that matters is past
that. The whole caution is pinned here. The hook's preamble was pinned here too
until 2026-09-13, when the block stopped mirroring cc's and took a header of its
own -- there is no borrowed preamble left to go stale.

Each pin must appear in what its local author emits, and appear in the decompiled
source exactly as many times as recorded:

  absent from the decompiled source  this repo carries wording no release ships,
                                     so the rebase log in `sys_prompt/CLAUDE.md`
                                     is out of date
  absent from the local author       a borrowed passage was edited without
                                     recording the divergence
  a different number of times        Claude Code builds the two prompt bodies
                                     from separate literals, so a passage in
                                     both moves in one and not the other; a
                                     count that only has to be non-zero would
                                     still pass on the half that changed

Either way the answer is a decision, not an edit to this file: adopt upstream's
new wording, or diverge on purpose and move the pin to the "deliberate
divergences" list in `sys_prompt/CLAUDE.md`.

Pins cover only what this repo borrowed. Upstream text this prompt never carried
is invisible here — `sys_prompt/CLAUDE.md` covers finding that by diffing the
decompile across releases.

Exit 0 every pin resolves, 1 some do not, 2 the decompiled tree is missing or is
not the installed build — so a skipped re-extraction reports itself instead of
passing vacuously.
"""

import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PROMPT = REPO / "sys_prompt" / "alan-default-next.md"
DECOMPILED = Path("/repos/claude-code-decompiled/src")

# (label, occurrences in the decompiled tree, which local author must also carry
# it, verbatim text). Each text is cut to avoid `${...}` interpolation in the
# upstream template, which is why some start mid-sentence. The opening line
# occurs twice because Claude Code opens both its lean and its non-lean prompt
# body with it, from two separate literals.
PINS = [
    ("opening line", 2, "prompt", "You are an interactive agent that helps users with software engineering tasks."),
    ("harness/output", 1, "prompt", "Text you output outside of tool use is displayed to the user as Github-flavored markdown in a terminal."),
    ("harness/permission", 1, "prompt", "Tools run behind a user-selected permission mode; a denied call means the user declined it — adjust, don't retry verbatim."),
    ("harness/system-reminder", 1, "prompt", "`<system-reminder>` tags in messages and tool results are injected by the harness, not the user."),
    ("harness/hooks", 1, "prompt", "Hooks may intercept tool calls; treat hook output as user feedback."),
    ("harness/dedicated-tools", 1, "prompt", "Prefer the dedicated file/search tools over shell commands when one fits. Independent tool calls can run in parallel in one response."),
    ("harness/file-line", 1, "prompt", "Reference code as `file_path:line_number` — it's clickable."),
    ("care/confirm-first", 1, "prompt", "For actions that are hard to reverse or outward-facing, confirm first unless durably authorized or explicitly told to proceed without asking; approval in one context doesn't extend to the next. Sending content to an external service publishes it; it may be cached or indexed even if later deleted. Before deleting or overwriting, look at the target"),
    ("context-management", 1, "prompt", "When the conversation grows long, some or all of the current context is summarized; the summary, along with any remaining unsummarized context, is provided in the next context window so work can continue — you don't need to wrap up early or hand off mid-task."),
    ("guidance/bang-prefix", 1, "prompt", "If you need the user to run a shell command themselves (e.g., an interactive login like `gcloud auth login`), suggest they type `! <command>` in the prompt — the `!` prefix runs the command in this session so its output lands directly in the conversation."),
    ("guidance/subagents", 1, "prompt", "tool with specialized agents when the task at hand matches the agent's description. Subagents are valuable for parallelizing independent queries or for protecting the main context window from excessive results, but they should not be used excessively when not needed. Importantly, avoid duplicating work that subagents are already doing - if you delegate research to a subagent, do not also perform the same searches yourself."),
    ("guidance/explore", 1, "prompt", "For broad codebase exploration or research that'll take more than "),
    ("guidance/skills", 1, "prompt", "Only use skills listed in the user-invocable skills section — don't guess."),
    ("env/stash-caution", 1, "env-context", "The git stash stack is shared with the main checkout and all other worktrees, and other Claude sessions may push or pop it concurrently. Never use bare `git stash` / `git stash pop` — you could pop another session's changes. Prefer a temporary WIP commit to set work aside; if you must stash, use `git stash push -u -m \"<unique-tag>\"`, immediately capture your entry's SHA via `git stash list --format='%H %gs'`, restore with `git stash apply <sha>` (not pop), and afterwards drop the entry, re-finding its current `stash@{n}` by tag first."),
]

# The decompiled source escapes non-ASCII as \uXXXX, escapes backticks and dollar
# signs inside template literals, and escapes whichever quote encloses a string —
# the stash caution contains `"<unique-tag>"` and reaches the source as
# `\"<unique-tag>\"`. Surrogate pairs are matched as one unit so a non-BMP
# character decodes to the character rather than to two lone surrogates. One
# left-to-right pass, so a literal backslash consumes the character after it
# instead of a later alternative matching across it.
_ESCAPE = re.compile(
    r"\\u([dD][89abAB][0-9a-fA-F]{2})\\u([dD][c-fC-F][0-9a-fA-F]{2})"
    r"|\\u([0-9a-fA-F]{4})"
    r"|\\([`$\\\"'])"
)


def _unescape(text: str) -> str:
    def one(m: re.Match) -> str:
        if m.group(1):
            hi, lo = int(m.group(1), 16), int(m.group(2), 16)
            return chr(0x10000 + (hi - 0xD800) * 0x400 + (lo - 0xDC00))
        if m.group(3):
            return chr(int(m.group(3), 16))
        return m.group(4)

    return _ESCAPE.sub(one, text)


def _tree_version() -> str | None:
    cli = DECOMPILED / "cli.js"
    if not cli.is_file():
        return None
    with cli.open(encoding="utf-8", errors="replace") as fh:
        for line in fh:
            m = re.search(r'VERSION: "([^"]+)"', line)
            if m:
                return m.group(1)
    return None


def _installed_version() -> str | None:
    try:
        out = subprocess.run(
            ["claude", "--version"], capture_output=True, text=True, timeout=30
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if out.returncode != 0:
        return None
    return out.stdout.strip().split()[0] if out.stdout.strip() else None


def _authors() -> dict[str, str]:
    """What each local author actually emits, keyed by the name the pins use.

    `env-context` is rendered rather than read as source, so a pin has to survive
    the assembly as well as the constant: a borrowed sentence still in the file
    but no longer emitted would otherwise pass. Every optional bullet is switched
    on so no branch is skipped.
    """
    sys.path.insert(0, str(REPO / "src"))
    from claude_config.env_context import render

    return {
        "prompt": PROMPT.read_text(),
        "env-context": render.sections(
            {
                "cwd": "/w",
                "is_git_repo": True,
                "platform": "linux",
                "shell": "/bin/bash",
                "os_version": "Linux",
                "session_id": "s",
                "worktree_common_dir": "/main/.git",
                "model": "m",
                "scratchpad": "/scratch",
                "drift_note": "n",
            }
        ),
    }


def main() -> int:
    if not DECOMPILED.is_dir():
        print(f"decompiled tree not found: {DECOMPILED}", file=sys.stderr)
        return 2

    tree, installed = _tree_version(), _installed_version()
    if tree is None:
        print(f"no VERSION in {DECOMPILED / 'cli.js'}", file=sys.stderr)
        return 2
    if installed is None:
        print(
            "cannot run `claude --version`, so the decompiled tree cannot be "
            f"confirmed as the installed build (tree says {tree})",
            file=sys.stderr,
        )
        return 2
    if tree != installed:
        print(
            f"decompiled tree is {tree}, installed Claude Code is {installed} — "
            "re-extract before trusting this check",
            file=sys.stderr,
        )
        return 2

    authors = _authors()
    counts = {label: 0 for label, _, _, _ in PINS}
    for path in sorted(DECOMPILED.rglob("*.js")):
        body = _unescape(path.read_text(encoding="utf-8", errors="replace"))
        for label, _, _author, text in PINS:
            counts[label] += body.count(text)

    bad = 0
    for label, want, author, text in PINS:
        if text not in authors[author]:
            print(f"NOT IN {author.upper()}  {label}")
            bad += 1
        if counts[label] != want:
            print(f"IN SOURCE {counts[label]}x, EXPECTED {want}x  {label}")
            bad += 1

    if bad:
        print(
            f"\n{bad} problem(s) across {len(PINS)} borrowed passages — "
            "see sys_prompt/CLAUDE.md, 'Rebasing on an upstream release'",
            file=sys.stderr,
        )
        return 1
    print(f"OK: {len(PINS)} borrowed passages still match Claude Code {tree}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
