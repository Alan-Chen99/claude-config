#!/usr/bin/env bash
# Fail when a section of sys_prompt/CLAUDE.md's rationale names no text the
# prompt still carries.
#
# Each `###` under `## Why the prompt says what it says` explains one thing the
# prompt does. It owns that thing by quoting it: a backticked literal in the
# heading that occurs verbatim in the prompt. Delete the prompt line and the
# section stops matching, so the round that deletes the line is told to delete
# the paragraph — the file's section count is then a function of the prompt's
# size and cannot outgrow it, which is the property a token ceiling would
# otherwise have to be picked by hand to get.
#
# Sections that explain something other than a prompt line do not belong in that
# region; the ledger of dead wordings sits under its own `##` heading for that
# reason.
set -euo pipefail
root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

python3 - "$root/sys_prompt/CLAUDE.md" "$root/sys_prompt/alan-default-next.md" <<'PY'
import re
import sys

rationale, prompt = (open(p).read() for p in sys.argv[1:3])

REGION = "## Why the prompt says what it says"
if REGION not in rationale:
    sys.exit(f"{REGION!r} is gone; this check no longer describes the file.")

# A shorter literal matches by accident: `and`, `docs/`, a bare flag.
MIN_LITERAL = 5

region = rationale[rationale.index(REGION) :]
region = re.split(r"(?m)^## (?!Why the prompt)", region)[0]
flat = re.sub(r"\s+", " ", prompt)

unowned = []
headings = re.findall(r"(?m)^### (.*)$", region)
for heading in headings:
    quotes = [q for q in re.findall(r"`([^`\n]+)`", heading) if len(q) >= MIN_LITERAL]
    if not any(re.sub(r"\s+", " ", q) in flat for q in quotes):
        unowned.append(heading)

for heading in unowned:
    print(f"unowned: ### {heading}", file=sys.stderr)
if unowned:
    sys.exit(
        f"{len(unowned)} of {len(headings)} rationale sections name no live prompt text. "
        "Delete the section, or quote in its heading the prompt text it explains."
    )
print(f"rationale: {len(headings)} sections, each naming live prompt text")
PY
