#!/usr/bin/env bash
# Feed one case's stage-1 artifact to a downstream reader and record what the
# reader does with it.
#
#   scripts/prompt-test-cc-downstream.sh <case> <artifact-file> <tag>
#
# The case's downstream.md is the reader's task, with the literal marker
# {{ARTIFACT}} replaced by the contents of <artifact-file>. Stage 1 measures what
# the sender wrote; this measures what it costs the receiver, which is the only
# place a handoff defect becomes an action.
#
# The reader is deliberately NOT this checkout's harness: stock Claude Code
# prompt, a fresh empty CLAUDE_CONFIG_DIR, no plugins, no hooks, no CLAUDE.md.
# Holding the reader constant is what makes the arms comparable, and a reader
# running the prompt under test could repair a defective artifact from its own
# instructions and hide the effect being measured.
set -euo pipefail

REPO="$(cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")/.." && pwd)"
CASE="${1:?usage: prompt-test-cc-downstream.sh <case> <artifact-file> <tag>}"
ARTIFACT="${2:?usage: prompt-test-cc-downstream.sh <case> <artifact-file> <tag>}"
TAG="${3:?usage: prompt-test-cc-downstream.sh <case> <artifact-file> <tag>}"

CASE_DIR="$REPO/prompt-tests/general/$CASE"
DOWNSTREAM="$CASE_DIR/downstream.md"
test -f "$DOWNSTREAM" || { echo "no downstream.md for case: $CASE_DIR" >&2; exit 1; }
test -f "$ARTIFACT" || { echo "no such artifact file: $ARTIFACT" >&2; exit 1; }

ENV_FILE="${PROMPT_TEST_ENV_FILE:-/workspace/.env}"
test -f "$ENV_FILE" || { echo "no env file at $ENV_FILE (needs CLAUDE_CODE_OAUTH_TOKEN)" >&2; exit 1; }
set -a; . "$ENV_FILE"; set +a
test -n "${CLAUDE_CODE_OAUTH_TOKEN:-}" || { echo "CLAUDE_CODE_OAUTH_TOKEN unset after sourcing $ENV_FILE" >&2; exit 1; }

OUT_DIR="${PROMPT_TEST_OUT_DIR:-/tmp/prompt-test-logs}"
mkdir -p "$OUT_DIR"
# Neutral name: see prompt-test-cc.sh for why the cwd carries no case name.
SCRATCH="$(mktemp -d "/tmp/ptcc-down.XXXXXXXX")"
CFG="$SCRATCH/.cfg"
mkdir -p "$CFG"
OUT="$OUT_DIR/${CASE}-downstream-${TAG}-$(basename "$SCRATCH" | sed 's/.*\.//').json"

PROMPT="$SCRATCH/prompt.md"
python3 - "$DOWNSTREAM" "$ARTIFACT" "$PROMPT" <<'PY'
import sys
tpl = open(sys.argv[1]).read()
art = open(sys.argv[2]).read().strip()
if "{{ARTIFACT}}" not in tpl:
    sys.exit("downstream.md has no {{ARTIFACT}} marker")
open(sys.argv[3], "w").write(tpl.replace("{{ARTIFACT}}", art))
PY

# 2.1.257 made `claude -p` wait for an armed Monitor instead of exiting once its
# result is in, so an unbounded call can outlive the run it belongs to with
# nothing to say so. No case text names Monitor, but the model decides whether to
# arm one, so the bound is on the call rather than on the cases. `agent-tools
# claude` and `claude.sh` both exec, so the process `timeout` signals is claude
# itself. Raise it for a case that legitimately runs longer:
#   PROMPT_TEST_TIMEOUT=3600 scripts/prompt-test-cc.sh ...
TIMEOUT="${PROMPT_TEST_TIMEOUT:-900}"

status=0
( cd "$SCRATCH" && CLAUDE_CONFIG_DIR="$CFG" timeout --kill-after=30 "$TIMEOUT" claude \
    -p --output-format json --dangerously-skip-permissions \
    --thinking-display summarized \
    < "$PROMPT" > "$OUT" ) 2>"$OUT.stderr" || status=$?
if [ "$status" -eq 124 ]; then
    echo "claude -p exceeded ${TIMEOUT}s and was killed; raise PROMPT_TEST_TIMEOUT" >&2
    exit 124
fi
if [ "$status" -ne 0 ]; then
    echo "claude -p exited $status; see $OUT.stderr" >&2
    exit "$status"
fi

echo "case:       $CASE (downstream)"
echo "tag:        $TAG"
echo "artifact:   $ARTIFACT"
echo "result:     $OUT"
echo "prompt:     $PROMPT"
echo "scratch:    $SCRATCH"
