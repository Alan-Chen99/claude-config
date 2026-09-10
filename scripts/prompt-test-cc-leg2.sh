#!/usr/bin/env bash
# Send a case's second-leg instruction to a session prompt-test-cc.sh already ran.
#
#   scripts/prompt-test-cc-leg2.sh <case> <session-id> <scratch-dir> <tag> [prompt-file]
#
# <session-id> and <scratch-dir> are both printed by prompt-test-cc.sh.
#
# The leg has to be a second turn rather than a second invocation. A case whose
# second leg cuts what its first leg wrote is measuring whether the agent spares
# text it remembers writing, and a fresh session has nothing to spare.
#
# Resuming needs the original cwd: the artifact is a file in that scratch
# directory, and the session's own tool history refers to it by path.
set -euo pipefail

REPO="$(cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")/.." && pwd)"
CASE="${1:?usage: prompt-test-cc-leg2.sh <case> <session-id> <scratch-dir> <tag> [prompt-file]}"
SID="${2:?missing session-id — prompt-test-cc.sh prints it as 'session:'}"
SCRATCH="${3:?missing scratch-dir — prompt-test-cc.sh prints it as 'scratch:'}"
TAG="${4:?missing tag}"
PROMPT_FILE="${5:-$REPO/sys_prompt/alan-default-next.md}"

CASE_DIR="$REPO/prompt-tests/general/$CASE"
LEG2="$CASE_DIR/leg2.md"
test -f "$LEG2" || { echo "no leg2.md for case: $CASE_DIR" >&2; exit 1; }
test -d "$SCRATCH" || { echo "scratch dir is gone: $SCRATCH" >&2; exit 1; }
test -f "$PROMPT_FILE" || { echo "no such prompt file: $PROMPT_FILE" >&2; exit 1; }
PROMPT_FILE="$(readlink -f "$PROMPT_FILE")"

head -1 "$PROMPT_FILE" | grep -qx -- '---' && {
  echo "$PROMPT_FILE starts with YAML frontmatter; strip it before testing" >&2
  exit 1
}

ENV_FILE="${PROMPT_TEST_ENV_FILE:-/workspace/.env}"
test -f "$ENV_FILE" || { echo "no env file at $ENV_FILE (needs CLAUDE_CODE_OAUTH_TOKEN)" >&2; exit 1; }
set -a; . "$ENV_FILE"; set +a
test -n "${CLAUDE_CODE_OAUTH_TOKEN:-}" || { echo "CLAUDE_CODE_OAUTH_TOKEN unset after sourcing $ENV_FILE" >&2; exit 1; }

AT="$REPO/agent-tools/target/release/agent-tools"
test -x "$AT" || { echo "build the worktree binary first: (cd $REPO/agent-tools && cargo build --release)" >&2; exit 1; }

# The settings file prompt-test-cc.sh wrote is still in the scratch dir; reuse it
# so plugin state matches leg 1 exactly.
SETTINGS="$SCRATCH/.prompt-test-settings.json"
test -f "$SETTINGS" || { echo "no $SETTINGS — was this scratch dir written by prompt-test-cc.sh?" >&2; exit 1; }

OUT_DIR="${PROMPT_TEST_OUT_DIR:-/tmp/prompt-test-logs}"
mkdir -p "$OUT_DIR"
OUT="$OUT_DIR/${CASE}-${TAG}-leg2.json"

( cd "$SCRATCH" && CLAUDE_CONFIG_ROOT="$REPO" "$AT" claude \
    -p --output-format json \
    --resume "$SID" \
    --thinking-display summarized \
    --settings "$SETTINGS" \
    --system-prompt-file "$PROMPT_FILE" \
    < "$LEG2" > "$OUT.raw" ) 2>"$OUT.stderr"
sed -n '/^{/,$p' "$OUT.raw" > "$OUT"

SID2="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1])).get("session_id",""))' "$OUT")"
TRANSCRIPT="$(find "$REPO/.claude/worktree-config/projects" -name "$SID2.jsonl" 2>/dev/null | head -1)"

echo "case:       $CASE (leg 2)"
echo "tag:        $TAG"
echo "resumed:    $SID"
echo "result:     $OUT"
echo "transcript: ${TRANSCRIPT:-<not found>}"
echo "scratch:    $SCRATCH"
echo "session:    $SID2"
