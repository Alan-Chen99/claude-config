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
CLAUDE_SH_SELF="$(readlink -f "${BASH_SOURCE[0]}")"
REPO_DIR="$(cd "$(dirname "$CLAUDE_SH_SELF")/.." && pwd)"

# The chain of launchers that configured this session, in order, appended by
# each one it passes through. `agent-tools hook-provenance` records it into the
# transcript; nothing else can recover it, because the `exec` below replaces
# this shell and leaves no process to walk back to. Assigned before the export
# so a failed `readlink` is not masked by `export`'s own exit status, which
# would hand the chain a truncated entry under `set -e`.
export CLAUDE_SH_LAUNCHERS="${CLAUDE_SH_LAUNCHERS:+$CLAUDE_SH_LAUNCHERS:}$CLAUDE_SH_SELF"

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

# `[1m]` is Claude Code syntax rather than part of the id: the request's model
# field is `tA(model)` (`src/chunk-j0tbz6ra.js:112632`), which strips the suffix
# (`$n()`, `/\[(1|2)m\]/gi`, `src/chunk-ya7n419k.js:30`), and the endpoint
# rejects it unstripped — `glm-5.3[1m]` answers 400 `[1211][Unknown Model,
# please check the model code.]`. The test mirrors cc's own, which is
# case-insensitive and matches anywhere in the string (`K2t()`, `/\[1m\]/i`,
# `src/chunk-ajtyjx88.js:21371`).
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
	# CLAUDE_CODE_AUTO_COMPACT_WINDOW also reads `k`/`M` suffixes (2.1.304), but
	# this variable parses an integer with `parseInt`: `200k` is 200 tokens to it.
	[[ "$ZAI_CONTEXT_TOKENS" =~ ^[1-9][0-9]*$ ]] || {
		echo "zai.sh: ZAI_CONTEXT_TOKENS='$ZAI_CONTEXT_TOKENS' is not a plain token count; give it as digits alone, such as 200000" >&2
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
# Stating it settles where the compact threshold comes from: `TS()`
# (`src/chunk-j0tbz6ra.js:64296`) takes this variable ahead of a settings
# value, clientdata, an experiment and the model defaults, and the effective
# threshold is the smaller of it and the context window. cc caps it at
# 1,000,000, where the derived default sits: above that it warns at startup
# that the value "is too large" and uses the cap, so a larger
# ZAI_CONTEXT_TOKENS is clamped here. The length test keeps a number past
# bash's 64-bit arithmetic from wrapping.
COMPACT_WINDOW="$ZAI_CONTEXT_TOKENS"
((${#COMPACT_WINDOW} <= 7 && COMPACT_WINDOW <= 1000000)) || COMPACT_WINDOW=1000000
export CLAUDE_CODE_AUTO_COMPACT_WINDOW="$COMPACT_WINDOW"

# Z.ai's own Claude Code configuration raises the per-request timeout to this,
# from cc's 600,000 ms default. cc applies no ceiling of its own, so the number
# passes through as written. Whether a GLM-5.3 turn at its default `max` effort
# actually reaches 600,000 ms is not measured here.
export API_TIMEOUT_MS="${API_TIMEOUT_MS:-3000000}"

# claude.sh fixes the git identity against the ambient environment; this is the
# one input it takes for it, so a commit says which model made it.
export CLAUDE_SH_AUTHOR_NAME="Claude(GLM)"

exec "${REPO_DIR}/scripts/claude.sh" "$@"
