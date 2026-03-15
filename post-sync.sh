#!/usr/bin/env bash
# post-sync.sh — Run after syncing with upstream to patch paths.
#
# Upstream uses relative .claude/ paths in working-dir attributes.
# This repo needs ~/.claude/ (absolute home-relative) paths instead.
#
# Usage: ./post-sync.sh [--dry-run]

set -euo pipefail
cd "$(dirname "$0")"

DRY_RUN=false
if [[ "${1:-}" == "--dry-run" ]]; then
    DRY_RUN=true
fi

count=0

patch_file() {
    local file="$1"
    if grep -qF 'working-dir=".claude' "$file" 2>/dev/null; then
        if $DRY_RUN; then
            echo "[dry-run] would patch: $file"
            grep -nF 'working-dir=".claude' "$file"
        else
            sed -i 's|working-dir="\.claude|working-dir="~/.claude|g' "$file"
            echo "patched: $file"
        fi
        count=$((count + 1))
    fi
}

# Patch all markdown and python files containing working-dir=".claude
while IFS= read -r -d '' file; do
    patch_file "$file"
done < <(find . -type f \( -name '*.md' -o -name '*.py' \) -not -path './.git/*' -print0)

# Also patch the InvokeAfterNode default in nodes.py
NODES="skills/scripts/skills/lib/workflow/ast/nodes.py"
if [[ -f "$NODES" ]]; then
    if grep -qF 'working_dir: str = ".claude' "$NODES" 2>/dev/null; then
        if $DRY_RUN; then
            echo "[dry-run] would patch default in: $NODES"
        else
            sed -i 's|working_dir: str = "\.claude|working_dir: str = "~/.claude|g' "$NODES"
            echo "patched default: $NODES"
        fi
        count=$((count + 1))
    fi
fi

if [[ $count -eq 0 ]]; then
    echo "nothing to patch (already up to date)"
else
    echo "patched $count file(s)"
fi
