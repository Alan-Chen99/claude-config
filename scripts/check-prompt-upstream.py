#!/usr/bin/env python3
"""Check the prompt text this repo borrows from Claude Code against the installed
build.

`--system-prompt-file` replaces every system-prompt block but the one-line identity
block, so `sys_prompt/alan-default-next.md` supplies the whole prompt, and it carries
passages lifted from upstream, whose own copy is their only source of truth — and
upstream rewords prose between releases. That is what this script pins, along with
general-purpose's prompt, which each `agents/gp-*.md` copies whole and differs from
only in frontmatter. The SessionStart hook in `src/claude_config/env_context/`
borrows nothing: since 2.1.269 Claude Code delivers its own environment block
through `messages[]`, and the hook's block carries only what that one does not
(`env_context/render.py` names the duplicates it dropped).

Each pin must appear in the file that borrows it, and appear in the decompiled
source exactly as many times as recorded:

  absent from the decompiled source  this repo carries wording no release ships,
                                     so a rebase is due (`docs/prompt-rebase.md`)
  absent from the borrowing file     a borrowed passage was edited without
                                     recording the divergence
  a different number of times        Claude Code builds the two prompt bodies
                                     from separate literals, so a passage in
                                     both moves in one and not the other; a
                                     count that only has to be non-zero would
                                     still pass on the half that changed

Either way the answer is a decision, not an edit to this file: adopt upstream's
new wording, or diverge on purpose and move the pin to the "deliberate
divergences" list in `docs/prompt-rebase.md`.

Pins cover only what this repo borrowed. Upstream text this prompt never carried
is invisible here — `docs/prompt-rebase.md` covers finding that by diffing the
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
DECOMPILED = Path("/repos/claude-code-decompiled/src")

# The built-in's `getSystemPrompt` interpolates its opening sentence and its
# strengths-and-guidelines block, so the body is three pins joined by " " and "\n\n".
GENERAL_PURPOSE = [
    ("general-purpose/opening", 2, "You are an agent for Claude Code, Anthropic's official CLI for Claude. Given the user's message, you should use the tools available to complete the task. Complete the task fully—don't gold-plate, but don't leave it half-done."),
    ("general-purpose/report", 2, "When you complete the task, respond with a concise report covering what was done and any key findings — the caller will relay this to the user, so it only needs the essentials."),
    ("general-purpose/strengths-guidelines", 1, """Your strengths:
- Searching for code, configurations, and patterns across large codebases
- Analyzing multiple files to understand system architecture
- Investigating complex questions that require exploring many files
- Performing multi-step research tasks

Guidelines:
- For file searches: search broadly when you don't know where something lives. Use Read when you know the specific file path.
- For analysis: Start broad and narrow down. Use multiple search strategies if the first doesn't yield results.
- Be thorough: Check multiple locations, consider different naming conventions, look for related files.
- NEVER create files unless they're absolutely necessary for achieving your goal. ALWAYS prefer editing an existing file to creating a new one.
- NEVER proactively create documentation files (*.md) or README files. Only create documentation files if explicitly requested.
- You are already the dedicated agent for this task. Do the work directly — do not re-delegate your entire assignment to another single subagent."""),
]

# Borrowing file (relative to the repo) -> (label, occurrences in the decompiled
# tree, verbatim text). Each text is cut to avoid `${...}` interpolation in the
# upstream template, which is why some start mid-sentence. The system prompt's
# opening line occurs once though both prompt bodies open with it: since 2.1.310
# they share one literal.
PINS = {
    "sys_prompt/alan-default-next.md": [
        ("opening line", 1, "You are an agent working with the user toward their goals, using your own judgment along the way."),
        ("harness/output", 1, "Text you output outside of tool use is displayed to the user as Github-flavored markdown in a terminal."),
        ("harness/permission", 1, "Tools run behind a user-selected permission mode; a denied call means the user declined it — adjust, don't retry verbatim."),
        ("harness/system-reminder", 1, "`<system-reminder>` tags in messages and tool results are injected by the harness, not the user."),
        ("harness/hooks", 1, "Hooks may intercept tool calls; treat hook output as user feedback."),
        ("harness/dedicated-tools", 1, "Prefer the dedicated file/search tools over shell commands when one fits. Independent tool calls can run in parallel in one response."),
        ("harness/file-line", 1, "Reference code as `file_path:line_number` — it's clickable."),
        ("care/confirm-first", 1, "For actions that are hard to reverse or outward-facing, confirm first unless durably authorized or explicitly told to proceed without asking; approval in one context doesn't extend to the next. Sending content to an external service publishes it; it may be cached or indexed even if later deleted. Before deleting or overwriting, look at the target"),
        ("context-management", 1, "When the conversation grows long, some or all of the current context is summarized; the summary, along with any remaining unsummarized context, is provided in the next context window so work can continue — you don't need to wrap up early or hand off mid-task."),
        ("guidance/bang-prefix", 1, "If you need the user to run a shell command themselves (e.g., an interactive login like `gcloud auth login`), suggest they type `! <command>` in the prompt — the `!` prefix runs the command in this session so its output lands directly in the conversation."),
        ("guidance/skills", 1, "Only use skills listed in the user-invocable skills section — don't guess."),
    ],
    "agents/gp-opus48.md": GENERAL_PURPOSE,
    "agents/gp-cache1h.md": GENERAL_PURPOSE,
}

# The decompiled source escapes non-ASCII as \uXXXX, escapes backticks and dollar
# signs inside template literals, and escapes whichever quote encloses a string.
# Surrogate pairs are matched as one unit so a non-BMP character decodes to the
# character rather than to two lone surrogates. One left-to-right pass, so a
# literal backslash consumes the character after it instead of a later
# alternative matching across it.
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

    pins = {(label, want, text) for rows in PINS.values() for label, want, text in rows}
    counts = {text: 0 for _, _, text in pins}
    for path in sorted(DECOMPILED.rglob("*.js")):
        body = _unescape(path.read_text(encoding="utf-8", errors="replace"))
        for text in counts:
            counts[text] += body.count(text)

    bad = 0
    for borrower, rows in PINS.items():
        borrowed = (REPO / borrower).read_text()
        for label, _, text in rows:
            if text not in borrowed:
                print(f"NOT IN {borrower}  {label}")
                bad += 1
    for label, want, text in sorted(pins):
        if counts[text] != want:
            print(f"IN SOURCE {counts[text]}x, EXPECTED {want}x  {label}")
            bad += 1

    if bad:
        print(
            f"\n{bad} problem(s) across {len(pins)} borrowed passages — "
            "see docs/prompt-rebase.md",
            file=sys.stderr,
        )
        return 1
    print(f"OK: {len(pins)} borrowed passages in {len(PINS)} files still match Claude Code {tree}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
