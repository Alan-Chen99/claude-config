#!/usr/bin/env bash
#
# Z.ai-backed launcher: the provider environment for Z.ai's
# Anthropic-compatible endpoint and a git identity naming the model, then
# claude.sh for everything a session needs whatever serves it — IS_SANDBOX, the
# agent-view flag, the scratch root, the proxy probe and the system prompt.

set -euo pipefail

# readlink -f resolves the ~/.local/bin/zai.sh symlink, so the claude.sh that
# runs is the sibling in the checkout this file physically lives in — the
# canonical repo through the installed symlink, a worktree's own pair when that
# copy is invoked by path.
REPO_DIR="$(cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")/.." && pwd)"

# ZAI_API_KEY comes from the container environment, not from disk:
# docker-compose.yml gives the personal-env service `env_file: ../.env`, so
# every line of /workspace/.env is exported before any shell starts. That file
# is read at container start, which is why a key added to it while the
# container is up will not be there.
test -n "${ZAI_API_KEY:-}" || {
	echo "zai.sh: ZAI_API_KEY is not set." >&2
	echo "  It reaches the container through docker-compose.yml's env_file: ../.env," >&2
	echo "  which is read once at container start. Add it there and restart." >&2
	exit 1
}

# The GLM Coding Plan serves two models, and Z.ai's own Claude Code mapping
# splits the tiers between them: GLM-5.3 for opus and sonnet, GLM-5.3-Flash for
# haiku. Flash is the multimodal one; GLM-5.3 is text-only, so an image reaches
# a model that can read it only on the haiku tier.
ZAI_MODEL="${ZAI_MODEL:-glm-5.3[1m]}"
ZAI_HAIKU_MODEL="${ZAI_HAIKU_MODEL:-glm-5.3-flash[1m]}"

# `[1m]` is Claude Code syntax rather than part of the id: claude strips it
# before the request (`Gt()`, `/\[1m\]$/i`) and the endpoint rejects it
# unstripped — `glm-5.3[1m]` answers 400 `[1211][Unknown Model, please check
# the model code.]`. The test mirrors cc's own, which is case-insensitive and
# matches anywhere in the string (`Df()`, `/\[1m\]/i`).
has_1m_window() { [[ "$1" =~ \[1[mM]\] ]]; }

# Claude Code reads a context size off the model name: the `[1m]` form returns
# exactly 1,000,000 and short-circuits ahead of CLAUDE_CODE_MAX_CONTEXT_TOKENS,
# which is why the default pair needs no window variable at all. Any other id
# lands on cc's 200,000 fallback for a name it does not recognize, so it has to
# state its own size — one number, shared by every tier, since that variable is
# not per-model.
if has_1m_window "$ZAI_MODEL" && has_1m_window "$ZAI_HAIKU_MODEL"; then
	ZAI_CONTEXT_TOKENS=1000000
else
	test -n "${ZAI_CONTEXT_TOKENS:-}" || {
		echo "zai.sh: ZAI_MODEL='$ZAI_MODEL' ZAI_HAIKU_MODEL='$ZAI_HAIKU_MODEL' — an id without the [1m] suffix" >&2
		echo "  gets Claude Code's 200,000-token default; set ZAI_CONTEXT_TOKENS alongside it." >&2
		exit 1
	}
	export CLAUDE_CODE_MAX_CONTEXT_TOKENS="$ZAI_CONTEXT_TOKENS"
fi

export ANTHROPIC_BASE_URL="https://api.z.ai/api/anthropic"

# The key travels as `Authorization: Bearer`, which the endpoint accepts.
# ANTHROPIC_API_KEY would reach it as `x-api-key`, equally accepted, but that
# variable is also what Claude Code's custom-key approval list in
# ~/.claude.json keys on, so it brings an approval decision along with it.
export ANTHROPIC_AUTH_TOKEN="$ZAI_API_KEY"

# The same env_file also exports CLAUDE_CODE_OAUTH_TOKEN. Clearing it, and
# ANTHROPIC_API_KEY with it, leaves one credential in play rather than an
# Anthropic one sitting in the environment of a session pointed at Z.ai.
unset ANTHROPIC_API_KEY CLAUDE_CODE_OAUTH_TOKEN

# Every tier is stated, the fable one Z.ai's mapping does not name included. The
# endpoint answers to any model string — `sonnet` and `claude-opus-4-5` both
# return 200 and echo the name back — so a tier left unmapped does not fail, it
# quietly takes the window Claude Code sizes for that Anthropic name.
# settings.json pins `"model": "opus"`; agents and skills name the other tiers.
export ANTHROPIC_MODEL="$ZAI_MODEL"
export ANTHROPIC_DEFAULT_OPUS_MODEL="$ZAI_MODEL"
export ANTHROPIC_DEFAULT_SONNET_MODEL="$ZAI_MODEL"
export ANTHROPIC_DEFAULT_FABLE_MODEL="$ZAI_MODEL"
export ANTHROPIC_DEFAULT_HAIKU_MODEL="$ZAI_HAIKU_MODEL"
export CLAUDE_CODE_SUBAGENT_MODEL="$ZAI_MODEL"

# Derived from the same number as the window so the two cannot drift apart.
# Stating it settles where the compact threshold comes from: `tw()` takes this
# variable ahead of a settings value, clientdata, an experiment and the model
# defaults, and the effective threshold is the smaller of it and the context
# window. cc caps it at 1,000,000: the derived default sits exactly there, and
# a larger ZAI_CONTEXT_TOKENS is capped rather than refused.
export CLAUDE_CODE_AUTO_COMPACT_WINDOW="$ZAI_CONTEXT_TOKENS"

# Z.ai's own Claude Code configuration raises the per-request timeout to this,
# from cc's 600,000 ms default. cc applies no ceiling of its own, so the number
# passes through as written. Whether a GLM-5.3 turn at its default `max` effort
# actually reaches 600,000 ms is not measured here.
export API_TIMEOUT_MS="${API_TIMEOUT_MS:-3000000}"

# claude.sh fixes the git identity against the ambient environment; this is the
# one input it takes for it, so a commit says which model made it.
export CLAUDE_SH_AUTHOR_NAME="Claude(GLM)"

exec "${REPO_DIR}/scripts/claude.sh" "$@"
