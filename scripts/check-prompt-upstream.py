#!/usr/bin/env python3
"""Check the passages `sys_prompt/alan-default-next.md` borrows from Claude Code's
own system prompt against the installed build.

`--system-prompt-file` replaces every system-prompt block but the one-line
identity block, so none of Claude Code's prompt text reaches such a session. The
passages pinned below are there because this repo copied them; upstream's own
copy is their only source of truth, and upstream rewords prose between releases.

Each pin must appear verbatim on both sides:

  absent from the decompiled source  the prompt carries wording no release
                                     ships, so the rebase log in
                                     `sys_prompt/CLAUDE.md` is out of date
  absent from the prompt             a borrowed passage was edited without
                                     recording the divergence

Either way the answer is a decision, not an edit to this file: adopt upstream's
new wording, or diverge on purpose and move the pin to the "deliberate
divergences" list in `sys_prompt/CLAUDE.md`.

Pins cover only what this repo borrowed. Upstream text this prompt never carried
is invisible here — `sys_prompt/CLAUDE.md` covers finding that by diffing the
decompile across releases.

Exit 0 every pin resolves, 1 some do not, 2 no decompiled tree — so a skipped
re-extraction reports itself instead of passing vacuously.
"""

import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PROMPT = REPO / "sys_prompt" / "alan-default-next.md"
DECOMPILED = Path("/repos/claude-code-decompiled/src")

# (label, verbatim text). Each is cut to avoid `${...}` interpolation in the
# upstream template, which is why some start mid-sentence.
PINS = [
    ("opening line", "You are an interactive agent that helps users with software engineering tasks."),
    ("harness/output", "Text you output outside of tool use is displayed to the user as Github-flavored markdown in a terminal."),
    ("harness/permission", "Tools run behind a user-selected permission mode; a denied call means the user declined it — adjust, don't retry verbatim."),
    ("harness/system-reminder", "`<system-reminder>` tags in messages and tool results are injected by the harness, not the user."),
    ("harness/hooks", "Hooks may intercept tool calls; treat hook output as user feedback."),
    ("harness/dedicated-tools", "Prefer the dedicated file/search tools over shell commands when one fits. Independent tool calls can run in parallel in one response."),
    ("harness/file-line", "Reference code as `file_path:line_number` — it's clickable."),
    ("care/confirm-first", "For actions that are hard to reverse or outward-facing, confirm first unless durably authorized or explicitly told to proceed without asking; approval in one context doesn't extend to the next. Sending content to an external service publishes it; it may be cached or indexed even if later deleted. Before deleting or overwriting, look at the target"),
    ("context-management", "When the conversation grows long, some or all of the current context is summarized; the summary, along with any remaining unsummarized context, is provided in the next context window so work can continue — you don't need to wrap up early or hand off mid-task."),
    ("guidance/bang-prefix", "If you need the user to run a shell command themselves (e.g., an interactive login like `gcloud auth login`), suggest they type `! <command>` in the prompt — the `!` prefix runs the command in this session so its output lands directly in the conversation."),
    ("guidance/subagents", "tool with specialized agents when the task at hand matches the agent's description. Subagents are valuable for parallelizing independent queries or for protecting the main context window from excessive results, but they should not be used excessively when not needed. Importantly, avoid duplicating work that subagents are already doing - if you delegate research to a subagent, do not also perform the same searches yourself."),
    ("guidance/explore", "For broad codebase exploration or research that'll take more than "),
    ("guidance/skills", "Only use skills listed in the user-invocable skills section — don't guess."),
]

# The decompiled source escapes non-ASCII as \uXXXX, and escapes backticks and
# dollar signs inside template literals. One left-to-right pass so that a
# literal backslash consumes the character after it rather than the next
# alternative matching across it.
_ESCAPE = re.compile(r"\\u([0-9a-fA-F]{4})|\\([`$\\])")


def _unescape(text: str) -> str:
    return _ESCAPE.sub(
        lambda m: chr(int(m.group(1), 16)) if m.group(1) else m.group(2), text
    )


def main() -> int:
    if not DECOMPILED.is_dir():
        print(f"decompiled tree not found: {DECOMPILED}", file=sys.stderr)
        return 2

    prompt = PROMPT.read_text()
    unresolved = [label for label, text in PINS if text not in prompt]
    for label in unresolved:
        print(f"NOT IN PROMPT  {label}")

    wanted = {label: text for label, text in PINS if label not in unresolved}
    found: set[str] = set()
    for path in sorted(DECOMPILED.rglob("*.js")):
        if len(found) == len(wanted):
            break
        body = _unescape(path.read_text(encoding="utf-8", errors="replace"))
        for label, text in wanted.items():
            if label not in found and text in body:
                found.add(label)

    for label in wanted:
        if label not in found:
            print(f"NOT IN SOURCE  {label}")

    missing = len(unresolved) + (len(wanted) - len(found))
    if missing:
        print(
            f"\n{missing} of {len(PINS)} borrowed passages unresolved — "
            f"see sys_prompt/CLAUDE.md, 'Rebasing on an upstream release'",
            file=sys.stderr,
        )
        return 1
    print(f"OK: {len(PINS)} borrowed passages still match the installed build")
    return 0


if __name__ == "__main__":
    sys.exit(main())
