#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
CLAUDE_DIR="${HOME}/.claude"
OPENCODE_DIR="${HOME}/.config/opencode"

# Directories to symlink
DIRS=(agents conventions output-styles skills)

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

src="${REPO_DIR}/opencode"
dst="${OPENCODE_DIR}"
if [ -d "$src" ]; then
    if [ -e "$dst" ] && [ ! -L "$dst" ]; then
        echo "error: $dst exists and is not a symlink -- remove it manually"
        exit 1
    fi

    mkdir -p "$(dirname "$dst")"
    ln -sfn "$src" "$dst"
    echo "linked: $dst -> $src"
fi

# Build and install agent-tools binary.
# IMPORTANT: Only the canonical repo (/repos/claude-config) should install here.
# Worktrees must NEVER install their build into ~/.local/bin — the symlink must
# always point to the canonical repo's release binary so that all sessions share
# a single, up-to-date binary regardless of which worktree is active.
AGENT_TOOLS_DIR="${REPO_DIR}/agent-tools"
AGENT_TOOLS_DST="${HOME}/.local/bin/agent-tools"
if [ -f "${AGENT_TOOLS_DIR}/Cargo.toml" ]; then
    if command -v cargo >/dev/null 2>&1; then
        echo "building agent-tools..."
        (cd "$AGENT_TOOLS_DIR" && cargo build --release --quiet)
        mkdir -p "${HOME}/.local/bin"
        ln -sf "${AGENT_TOOLS_DIR}/target/release/agent-tools" "$AGENT_TOOLS_DST"
        echo "installed: $AGENT_TOOLS_DST -> ${AGENT_TOOLS_DIR}/target/release/agent-tools"
    else
        echo "warning: cargo not found, skipping agent-tools build"
    fi
fi
