#!/usr/bin/env bash
# probe runner: <scratch-dir> <prompt-file> <tag> [--resume <sid>]
set -euo pipefail
REPO=/root/claude-config-work2
set -a; . /workspace/.env; set +a
AT="$REPO/agent-tools/target/release/agent-tools"
SCRATCH="$1"; TASK="$2"; TAG="$3"; shift 3
OUT="/tmp/prompt-test-logs/probe-$TAG.json"
python3 - "$REPO/settings.json" "$SCRATCH/.prompt-test-settings.json" <<'PY'
import json, sys
plugins = json.load(open(sys.argv[1])).get("enabledPlugins", {})
json.dump({"enabledPlugins": {k: False for k in plugins}}, open(sys.argv[2], "w"))
PY
( cd "$SCRATCH" && CLAUDE_CONFIG_ROOT="$REPO" "$AT" claude \
    -p --output-format json --thinking-display summarized \
    --settings "$SCRATCH/.prompt-test-settings.json" \
    --system-prompt-file /tmp/wfoa-arms/prompt-ablated.md \
    "$@" < "$TASK" > "$OUT.raw" ) 2>"$OUT.stderr"
sed -n '/^{/,$p' "$OUT.raw" > "$OUT"
SID="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1])).get("session_id",""))' "$OUT")"
echo "tag: $TAG  session: $SID"
echo "transcript: $(find "$REPO/.claude/worktree-config/projects" -name "$SID.jsonl" 2>/dev/null | head -1)"
