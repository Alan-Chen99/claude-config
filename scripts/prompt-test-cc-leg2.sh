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

case "$CASE" in
  */*) CASE_DIR="$CASE" ;;
  *)   CASE_DIR="$REPO/prompt-tests/general/$CASE" ;;
esac
CASE_LABEL="$(basename "$CASE")"
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

# Rebuilt rather than reused: leg 1's settings file is written outside the
# scratch cwd and removed when that run exits, because a file named for the
# harness inside the agent's own working directory tells it what it is inside.
# Both legs derive it from the same source, so plugin state still matches.
SETTINGS="$(mktemp "/tmp/cfg.XXXXXXXX.json")"
trap 'rm -f "$SETTINGS"' EXIT
python3 - "$REPO/settings.json" "$SETTINGS" <<'PY_SETTINGS'
import json, sys
src, dst = sys.argv[1], sys.argv[2]
plugins = json.load(open(src)).get("enabledPlugins", {})
json.dump({"enabledPlugins": {k: False for k in plugins}}, open(dst, "w"))
PY_SETTINGS

OUT_DIR="${PROMPT_TEST_OUT_DIR:-/tmp/prompt-test-logs}"
mkdir -p "$OUT_DIR"
OUT="$OUT_DIR/${CASE_LABEL}-${TAG}-leg2.json"

# Leg 2 edits leg 1's artifact in place, so leg 1's is gone the moment this runs
# and the pair cannot be scored. Snapshot first.
SNAP="$OUT_DIR/${CASE_LABEL}-${TAG}-leg1-artifacts"
if [ -d "$SNAP" ]; then
  echo "leg-1 snapshot already exists, refusing to overwrite: $SNAP" >&2
  exit 1
fi
mkdir -p "$SNAP"
find "$SCRATCH" -maxdepth 1 -type f -exec cp -a {} "$SNAP/" \;
echo "leg-1 snapshot: $SNAP"

# Since cc 2.1.267 a resume replays the system prompt recorded on the first
# request, whatever a later launch passes (GWe, src/chunk-dbb93264.js:130178);
# without this flag the arm file above is validated and then ignored. Measured
# on 2.1.269 through the proxy: a resume passing prompt B sent A; with the flag, B.
# 2.1.257 made `claude -p` wait for an armed Monitor instead of exiting once its
# result is in, so an unbounded call can outlive the run it belongs to with
# nothing to say so. No case text names Monitor, but the model decides whether to
# arm one, so the bound is on the call rather than on the cases. `agent-tools
# claude` and `claude.sh` both exec, so the process `timeout` signals is claude
# itself. Raise it for a case that legitimately runs longer:
#   PROMPT_TEST_TIMEOUT=3600 scripts/prompt-test-cc.sh ...
TIMEOUT="${PROMPT_TEST_TIMEOUT:-900}"

status=0
( cd "$SCRATCH" && CLAUDE_CONFIG_ROOT="$REPO" timeout --kill-after=30 "$TIMEOUT" "$AT" claude \
    -p --output-format json \
    --resume "$SID" \
    --thinking-display summarized \
    --settings "$SETTINGS" \
    --system-prompt-file "$PROMPT_FILE" \
    --system-prompt-snapshot off \
    < "$LEG2" > "$OUT.raw" ) 2>"$OUT.stderr" || status=$?
if [ "$status" -eq 124 ]; then
    echo "claude -p exceeded ${TIMEOUT}s and was killed; raise PROMPT_TEST_TIMEOUT" >&2
    exit 124
fi
if [ "$status" -ne 0 ]; then
    echo "claude -p exited $status; see $OUT.stderr" >&2
    exit "$status"
fi
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
