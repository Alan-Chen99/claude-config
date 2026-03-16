#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
HOOK_SRC="${REPO_DIR}/hooks/ntfy_hook.py"
HOOK_DST="${HOME}/.claude/hooks/ntfy_hook.py"

mkdir -p "$(dirname "$HOOK_DST")"

if [ -f "$HOOK_DST" ] && [ ! -L "$HOOK_DST" ]; then
    echo "error: $HOOK_DST exists as a regular file (not a symlink)"
    echo "remove it manually if you want to proceed"
    exit 1
fi

ln -sf "$HOOK_SRC" "$HOOK_DST"
echo "linked: $HOOK_DST -> $HOOK_SRC"
