#!/usr/bin/env bash
# Run one prompt-tests case against a full-replacement system prompt.
#
#   scripts/prompt-test-run.sh <case> <tag> [prompt-file]
#
# <case>        directory name under prompt-tests/general/
# <tag>         label for the output log, e.g. red / green / baseline
# [prompt-file] defaults to sys_prompt/alan-default-next.md
#
# The tested agent runs from a fresh /tmp scratch cwd with project config and
# plugins disabled, per .claude/skills/prompt-tests. A case's fixture/ directory,
# if present, is copied into that scratch cwd; nothing else from the repo is.
#
# To produce a baseline arm for a prompt edit, pass a committed copy of the
# prompt as the third argument:
#   git show HEAD:sys_prompt/alan-default-next.md > /tmp/prompt-baseline.md
#   scripts/prompt-test-run.sh <case> baseline /tmp/prompt-baseline.md
set -euo pipefail

REPO="$(cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")/.." && pwd)"
CASE="${1:?usage: prompt-test-run.sh <case> <tag> [prompt-file]}"
TAG="${2:?usage: prompt-test-run.sh <case> <tag> [prompt-file]}"
PROMPT_FILE="${3:-$REPO/sys_prompt/alan-default-next.md}"

CASE_DIR="$REPO/prompt-tests/general/$CASE"
test -d "$CASE_DIR" || { echo "no such case: $CASE_DIR" >&2; exit 1; }
test -f "$PROMPT_FILE" || { echo "no such prompt file: $PROMPT_FILE" >&2; exit 1; }

# A full-replacement prompt is loaded verbatim by opencode's {file:...}; YAML
# frontmatter would be injected as-is and leak whatever it says into the run.
head -1 "$PROMPT_FILE" | grep -qx -- '---' && {
  echo "$PROMPT_FILE starts with YAML frontmatter; strip it before testing" >&2
  exit 1
}

OUT_DIR="${PROMPT_TEST_OUT_DIR:-/tmp/prompt-test-logs}"
mkdir -p "$OUT_DIR"
# Neutral name: see prompt-test-cc.sh for why the cwd carries no case name.
SCRATCH="$(mktemp -d "/tmp/prompt-test.XXXXXXXX")"
OUT="$OUT_DIR/${CASE}-${TAG}.jsonl"

[ -d "$CASE_DIR/fixture" ] && cp -a "$CASE_DIR/fixture/." "$SCRATCH/"

set -a; . "$REPO/.env"; set +a

OPENCODE_DISABLE_PROJECT_CONFIG=1 \
OPENCODE_DISABLE_CLAUDE_CODE_PROMPT=1 \
OPENCODE_CONFIG_CONTENT='{
  "$schema": "https://opencode.ai/config.json",
  "plugin": [],
  "agent": {
    "prompt-test": {
      "mode": "primary",
      "model": "'"${PROMPT_TEST_MODEL:-openrouter/anthropic/claude-opus-5}"'",
      "prompt": "{file:'"$PROMPT_FILE"'}",
      "permission": {"read":"allow","glob":"allow","grep":"allow","list":"allow","bash":"allow","edit":"allow","write":"allow"}
    }
  }
}' \
  opencode run --agent prompt-test --format json --dir "$SCRATCH" \
    < "$CASE_DIR/task.md" > "$OUT"

echo "log:     $OUT"
echo "scratch: $SCRATCH"
grep -o '"sessionID":"[^"]*"' "$OUT" | head -1
