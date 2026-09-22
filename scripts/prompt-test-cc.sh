#!/usr/bin/env bash
# Run one prompt-tests case against a full-replacement system prompt under
# Claude Code.
#
#   scripts/prompt-test-cc.sh <case> <tag> [prompt-file]
#
# <case>        directory name under prompt-tests/general/
# <tag>         label for the output log, e.g. full / stripped / baseline
# [prompt-file] defaults to sys_prompt/alan-default-next.md
#
# Claude Code applies the LAST --system-prompt-file on the command line, so the
# arm file is appended after the one scripts/claude.sh passes; the launcher needs
# no argument of its own. Verified against the intercepted request body: a run
# with an override sends only the override's text as the system block.
#
# The tested agent runs from a fresh /tmp scratch cwd with plugins disabled, per
# .claude/skills/prompt-tests. A case's fixture/ directory, if present, is copied
# into that scratch cwd; nothing else from the repo is.
set -euo pipefail

REPO="$(cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")/.." && pwd)"
CASE="${1:?usage: prompt-test-cc.sh <case> <tag> [prompt-file]}"
TAG="${2:?usage: prompt-test-cc.sh <case> <tag> [prompt-file]}"
PROMPT_FILE="${3:-$REPO/sys_prompt/alan-default-next.md}"

CASE_DIR="$REPO/prompt-tests/general/$CASE"
test -d "$CASE_DIR" || { echo "no such case: $CASE_DIR" >&2; exit 1; }
test -f "$PROMPT_FILE" || { echo "no such prompt file: $PROMPT_FILE" >&2; exit 1; }
PROMPT_FILE="$(readlink -f "$PROMPT_FILE")"

# A case with more than one task wording runs its variants through the same
# fixture rather than through a copied case directory, so the fixtures cannot
# drift apart between arms that are meant to differ only in the instruction.
TASK_FILE="${PROMPT_TEST_TASK_FILE:-$CASE_DIR/task.md}"
case "$TASK_FILE" in /*) ;; *) TASK_FILE="$CASE_DIR/$TASK_FILE" ;; esac
test -f "$TASK_FILE" || { echo "no such task file: $TASK_FILE" >&2; exit 1; }

# --system-prompt-file loads the file verbatim, so YAML frontmatter would be
# injected as-is and leak whatever it says into the run.
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

OUT_DIR="${PROMPT_TEST_OUT_DIR:-/tmp/prompt-test-logs}"
mkdir -p "$OUT_DIR"
# The scratch cwd carries no case or tag name. The tested agent sees its own
# cwd -- in Claude Code's environment block, in its scratchpad path, and in
# every shell prompt -- so a directory named for what the case measures tells
# the agent what is being measured. Case names here describe the behaviour
# under test (halve-the-runbook, found-set-closure), which is the right name
# for a reader and the wrong one for the subject. Measured 2026-09-22: a case
# directory named for its question had the phrase back in both arms' delivered
# artifacts. The mapping from this directory to the case is printed below.
SCRATCH="$(mktemp -d "/tmp/ptcc.XXXXXXXX")"
OUT="$OUT_DIR/${CASE}-${TAG}-$(basename "$SCRATCH" | sed 's/.*\.//').json"

[ -d "$CASE_DIR/fixture" ] && cp -a "$CASE_DIR/fixture/." "$SCRATCH/"

# A case whose scratch cwd must be more than copied files -- a repository with
# history, say -- carries a setup.sh beside task.md. It runs in the scratch cwd
# and is never copied there, so nothing it says reaches the tested agent except
# what it leaves on disk. A failing setup fails the run.
[ -f "$CASE_DIR/setup.sh" ] && ( cd "$SCRATCH" && bash "$CASE_DIR/setup.sh" )

# Plugin defaults for prompt tests are "none loaded".
# A --settings file carrying only enabledPlugins adds no hook of its own, so the
# checkout's hooks stay registered exactly once.
#
# It lives outside the scratch cwd. A tested agent lists its own working
# directory, and a file there whose name contains "prompt-test" tells it what it
# is inside -- observed 2026-09-22, a run reporting the file by name as
# irrelevant harness config. The scratch directory is kept neutral for the same
# reason its name is.
SETTINGS="$(mktemp "/tmp/ptcfg.XXXXXXXX.json")"
trap 'rm -f "$SETTINGS"' EXIT
python3 - "$REPO/settings.json" "$SETTINGS" <<'PY'
import json, sys
src, dst = sys.argv[1], sys.argv[2]
plugins = json.load(open(src)).get("enabledPlugins", {})
json.dump({"enabledPlugins": {k: False for k in plugins}}, open(dst, "w"))
PY

# --thinking-display summarized is load-bearing. The default sends
# thinking.display="omitted", and every thinking block in the transcript is then
# an empty string with a signature and nothing else — the run looks complete and
# the reasoning it was read for is not in the file.
#
# `agent-tools claude` also runs check-prompt-coupling.sh, whose "prompt coupling
# OK" lands on the same stdout as the result JSON, so the raw stream is kept and
# the JSON cut out of it rather than the check being silenced.
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
    --thinking-display summarized \
    --settings "$SETTINGS" \
    --system-prompt-file "$PROMPT_FILE" \
    < "$TASK_FILE" > "$OUT.raw" ) 2>"$OUT.stderr" || status=$?
if [ "$status" -eq 124 ]; then
    echo "claude -p exceeded ${TIMEOUT}s and was killed; raise PROMPT_TEST_TIMEOUT" >&2
    exit 124
fi
if [ "$status" -ne 0 ]; then
    echo "claude -p exited $status; see $OUT.stderr" >&2
    exit "$status"
fi
sed -n '/^{/,$p' "$OUT.raw" > "$OUT"

SID="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1])).get("session_id",""))' "$OUT")"
TRANSCRIPT="$(find "$REPO/.claude/worktree-config/projects" -name "$SID.jsonl" 2>/dev/null | head -1)"

echo "case:       $CASE"
echo "tag:        $TAG"
echo "prompt:     $PROMPT_FILE"
echo "result:     $OUT"
echo "transcript: ${TRANSCRIPT:-<not found>}"
echo "scratch:    $SCRATCH"
echo "session:    $SID"
