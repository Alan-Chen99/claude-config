#!/usr/bin/env bash
#
# Kimi-backed launcher: the provider environment for Moonshot's
# Anthropic-compatible endpoint and a git identity naming the model, then
# claude.sh for everything a session needs whatever serves it — IS_SANDBOX, the
# agent-view flag, the scratch root, the proxy probe and the system prompt.

set -euo pipefail

# readlink -f resolves the ~/.local/bin/kimi.sh symlink, so the claude.sh that
# runs is the sibling in the checkout this file physically lives in — the
# canonical repo through the installed symlink, a worktree's own pair when that
# copy is invoked by path.
REPO_DIR="$(cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")/.." && pwd)"

# KIMI_API_KEY comes from the container environment, not from disk:
# docker-compose.yml gives the personal-env service `env_file: ../.env`, so
# every line of /workspace/.env is exported before any shell starts. That file
# is read at container start, which is why a key added to it while the
# container is up will not be there.
test -n "${KIMI_API_KEY:-}" || {
	echo "kimi.sh: KIMI_API_KEY is not set." >&2
	echo "  It reaches the container through docker-compose.yml's env_file: ../.env," >&2
	echo "  which is read once at container start. Add it there and restart." >&2
	exit 1
}

# `[1m]` is Claude Code syntax rather than part of the id: the API rejects
# `k3[1m]` with "Please set model id as `k3`", while claude sends `k3` and
# sizes the session at 1,000,000 tokens.
KIMI_MODEL="${KIMI_MODEL:-k3[1m]}"

# Claude Code reads a context size off the model name and falls back to 200,000
# for a name it does not recognize — measured: `k3-256k` reported a 200,000
# window with these two variables unset, 62,144 tokens short of what the model
# serves. Only the `[1m]` suffix carries a size of its own.
case "$KIMI_MODEL" in
'k3[1m]' | kimi-for-coding) MODEL_CONTEXT_TOKENS=1048576 ;;
k3-256k) MODEL_CONTEXT_TOKENS=262144 ;;
*) MODEL_CONTEXT_TOKENS="" ;;
esac
KIMI_CONTEXT_TOKENS="${KIMI_CONTEXT_TOKENS:-$MODEL_CONTEXT_TOKENS}"
test -n "$KIMI_CONTEXT_TOKENS" ||
	{ echo "kimi.sh: KIMI_MODEL='$KIMI_MODEL' has no known context size; set KIMI_CONTEXT_TOKENS alongside it" >&2; exit 1; }

export ANTHROPIC_BASE_URL="https://api.kimi.ai/coding/"

# The key travels as `Authorization: Bearer`, which the endpoint accepts.
# ANTHROPIC_API_KEY would reach it as `x-api-key`, equally accepted, but that
# variable is also what Claude Code's custom-key approval list in
# ~/.claude.json keys on, so it brings an approval decision along with it.
export ANTHROPIC_AUTH_TOKEN="$KIMI_API_KEY"

# The same env_file also exports CLAUDE_CODE_OAUTH_TOKEN. Clearing it, and
# ANTHROPIC_API_KEY with it, leaves one credential in play rather than an
# Anthropic one sitting in the environment of a session pointed at Kimi.
unset ANTHROPIC_API_KEY CLAUDE_CODE_OAUTH_TOKEN

# Every tier resolves to the one served model. The endpoint answers to any
# model string — `sonnet` and `claude-opus-4-5` both return 200 — so a tier
# left unmapped does not fail, it quietly takes the window Claude Code sizes
# for that Anthropic name. settings.json pins `"model": "opus"`; agents and
# skills name the other tiers.
export ANTHROPIC_MODEL="$KIMI_MODEL"
export ANTHROPIC_DEFAULT_OPUS_MODEL="$KIMI_MODEL"
export ANTHROPIC_DEFAULT_SONNET_MODEL="$KIMI_MODEL"
export ANTHROPIC_DEFAULT_HAIKU_MODEL="$KIMI_MODEL"
export ANTHROPIC_DEFAULT_FABLE_MODEL="$KIMI_MODEL"
export CLAUDE_CODE_SUBAGENT_MODEL="$KIMI_MODEL"

export CLAUDE_CODE_MAX_CONTEXT_TOKENS="$KIMI_CONTEXT_TOKENS"
export CLAUDE_CODE_AUTO_COMPACT_WINDOW="$KIMI_CONTEXT_TOKENS"
export CLAUDE_CODE_EFFORT_LEVEL="${CLAUDE_CODE_EFFORT_LEVEL:-high}"

# claude.sh fixes the git identity against the ambient environment; this is the
# one input it takes for it, so a commit says which model made it.
export CLAUDE_SH_AUTHOR_NAME="Claude(Kimi)"

exec "${REPO_DIR}/scripts/claude.sh" "$@"
