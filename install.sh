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

# Link systemd user units. Symlink only: enabling is left to a human, because a
# unit here can need machine-local state that no install step can provide —
# telegram-hitl.service will not start until a bot token exists at
# ~/.claude/channels/telegram/.env. Enabling it at install time on a machine
# without one would present as a service in `failed`.
SYSTEMD_SRC_DIR="${REPO_DIR}/systemd"
SYSTEMD_DST_DIR="${HOME}/.config/systemd/user"
if [ -d "$SYSTEMD_SRC_DIR" ]; then
    mkdir -p "$SYSTEMD_DST_DIR"
    for unit in "${SYSTEMD_SRC_DIR}"/*.service; do
        [ -e "$unit" ] || continue
        dst="${SYSTEMD_DST_DIR}/$(basename "$unit")"

        if [ -e "$dst" ] && [ ! -L "$dst" ]; then
            echo "error: $dst exists and is not a symlink -- remove it manually"
            exit 1
        fi

        ln -sf "$unit" "$dst"
        echo "linked: $dst -> $unit"
    done

    # Containers run no user manager, so the reload is conditional rather than
    # assumed; the symlinks above are still worth making there, since the same
    # $HOME may be a host bind mount.
    if systemctl --user show-environment >/dev/null 2>&1; then
        systemctl --user daemon-reload
        echo "reloaded: systemd user manager (enable a unit with: systemctl --user enable --now <name>)"
    else
        echo "note: no systemd user manager here, skipping daemon-reload"
    fi
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

# Put the launcher on PATH.
# IMPORTANT: canonical-repo-only, same rule as agent-tools above. A worktree that
# installs its own copy redirects every session's `claude.sh` to that worktree's
# scripts/claude.sh and sys_prompt/, and leaves a dangling symlink behind when the
# worktree is deleted.
CLAUDE_SH_SRC="${REPO_DIR}/scripts/claude.sh"
CLAUDE_SH_DST="${HOME}/.local/bin/claude.sh"
if [ -f "$CLAUDE_SH_SRC" ]; then
    mkdir -p "${HOME}/.local/bin"
    ln -sf "$CLAUDE_SH_SRC" "$CLAUDE_SH_DST"
    echo "installed: $CLAUDE_SH_DST -> $CLAUDE_SH_SRC"
fi

# Provision the canonical Python venv (mitmproxy + claude_config package).
#
# HIDDEN PATH DEPENDENCY — read before changing:
#   docker/entrypoint.sh (in the personal monorepo) starts mitmdump from a
#   hardcoded glob "${HOME}/.claude/venvs/claude-config*/bin/mitmdump". If the
#   canonical venv does not exist at exactly that name, nothing listens on
#   127.0.0.1:9160. scripts/claude.sh probes that port and skips HTTPS_PROXY
#   when it is dead, so sessions still run — they run unintercepted, with a
#   warning on stderr and no request logs under ~/.claude/requests-log.
#
# WHY UV_PROJECT_ENVIRONMENT IS PINNED HERE (not derived):
#   .envrc derives the venv name from `basename "$PWD"`, so running `uv sync`
#   from a worktree path (e.g. /root/claude-config-work) creates a venv named
#   "claude-config-work" instead of "claude-config". We pin the name explicitly
#   so the install step is location-independent — install.sh from any worktree
#   still provisions the canonical venv that entrypoint.sh expects.
#
# LEAKAGE STILL TO WATCH:
#   1. $HOME differs between host and container. The container's ~/.claude is
#      bind-mounted from /home/alan/personal/docker_home/.claude on the host.
#      A host-side `install.sh` does NOT provision the container's venv. This
#      step must run inside the dev container.
#   2. If a worktree's direnv triggers `uv sync` later, it will create a
#      sibling venv (e.g. claude-config-work). Harmless — entrypoint.sh's glob
#      prefers the canonical name alphabetically — but it does consume disk.
#   3. Renaming the canonical clone path away from "claude-config" breaks the
#      entrypoint glob. If you rename, update entrypoint.sh in lockstep.
if [ -f "${REPO_DIR}/pyproject.toml" ]; then
    if command -v uv >/dev/null 2>&1; then
        VENV_DIR="${CLAUDE_DIR}/venvs/claude-config"
        echo "syncing canonical venv at $VENV_DIR ..."
        # --reinstall-package claude-config forces the editable install to be
        # re-registered even when the package version is unchanged. Without it,
        # moving the canonical checkout (e.g. /repos/claude-config →
        # /home/alan/repos/claude-config) leaves the venv's direct_url.json and
        # .pth pointing at the old source path, so `import claude_config` keeps
        # loading from the stale prefix even after every other symlink and the
        # agent-tools binary resolve to the new one.
        (cd "$REPO_DIR" && UV_PROJECT_ENVIRONMENT="$VENV_DIR" uv sync --reinstall-package claude-config --quiet)
        echo "synced: $VENV_DIR"
    else
        echo "warning: uv not found, skipping venv sync (mitmproxy intercept will not start)"
    fi
fi
