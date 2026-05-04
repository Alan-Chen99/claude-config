#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
CLAUDE_DIR="${HOME}/.claude"

# Directories to symlink
DIRS=(agents conventions hooks output-styles skills)

# Files to symlink
FILES=(settings.json statusline.sh)

mkdir -p "$CLAUDE_DIR"

for dir in "${DIRS[@]}"; do
    src="${REPO_DIR}/${dir}"
    dst="${CLAUDE_DIR}/${dir}"
    [ ! -d "$src" ] && continue

    if [ -e "$dst" ] && [ ! -L "$dst" ]; then
        echo "error: $dst exists and is not a symlink -- remove it manually"
        exit 1
    fi

    ln -sfn "$src" "$dst"
    echo "linked: $dst -> $src"
done

for file in "${FILES[@]}"; do
    src="${REPO_DIR}/${file}"
    dst="${CLAUDE_DIR}/${file}"
    [ ! -f "$src" ] && continue

    if [ -e "$dst" ] && [ ! -L "$dst" ]; then
        echo "error: $dst exists and is not a symlink -- remove it manually"
        exit 1
    fi

    ln -sf "$src" "$dst"
    echo "linked: $dst -> $src"
done
