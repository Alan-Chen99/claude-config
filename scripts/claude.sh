#!/usr/bin/env bash

set -eux

# Fixed against the ambient environment rather than defaulted from it, so a
# GIT_AUTHOR_NAME already in the shell cannot end up on a commit. A sibling
# launcher names the model behind the session through CLAUDE_SH_AUTHOR_NAME --
# scripts/kimi.sh sets `Claude(Kimi)` -- and that is the only input taken.
export GIT_AUTHOR_NAME="${CLAUDE_SH_AUTHOR_NAME:-Claude}"
export GIT_AUTHOR_EMAIL="81847+claude@users.noreply.github.com"
export GIT_COMMITTER_NAME="$GIT_AUTHOR_NAME"
export GIT_COMMITTER_EMAIL="$GIT_AUTHOR_EMAIL"

export IS_SANDBOX=1
# Background/agent-view forks drop --system-prompt-file; closing the agent view
# closes every path that would otherwise run on the stock prompt.
export CLAUDE_CODE_DISABLE_AGENT_VIEW=1

# cc roots its scratchpad at CLAUDE_CODE_TMPDIR (AS(), chunk-tht8x923.js:19),
# for the main agent and for subagents alike, so redirecting it here is the only
# way both get one directory. The root follows $HOME rather than naming /tmp,
# because /tmp is container overlay and is lost on a rebuild while this
# container's home is a host bind mount.
# The same variable also roots plugin dirs, skill zips and the IPC socket dir;
# cc falls back to /tmp for the socket when the path is too long (jxr(),
# chunk-g92e0w45.js:567).
export CLAUDE_CODE_TMPDIR="$HOME/.claude/tmp"

# readlink -f resolves the ~/.local/bin/claude.sh symlink, so the prompt loaded
# belongs to the checkout the script physically lives in: the canonical repo via
# the installed symlink, or a worktree's own prompt when that copy is run by path.
REPO_DIR="$(cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")/.." && pwd)"

# Request interception is optional, and HTTPS_PROXY pointed at a dead listener
# fails every request with ECONNREFUSED, surfacing inside claude as "Unable to
# connect to Anthropic services". A TCP connect gates the proxy env so a missing
# proxy degrades to plain traffic with a warning instead of a broken session.
PROXY_HOST=127.0.0.1
PROXY_PORT=9160
if (exec 3<>"/dev/tcp/${PROXY_HOST}/${PROXY_PORT}") 2>/dev/null; then
	export HTTPS_PROXY="http://${PROXY_HOST}:${PROXY_PORT}"
	export NODE_EXTRA_CA_CERTS=~/.mitmproxy/mitmproxy-ca-cert.pem
	export NODE_OPTIONS="--use-env-proxy"
else
	echo "claude.sh: WARNING: nothing listening on ${PROXY_HOST}:${PROXY_PORT}; HTTPS_PROXY unset, requests are NOT intercepted. Start it with: python3 ${REPO_DIR}/scripts/intercept/run-proxy.py" >&2
fi

exec claude --dangerously-skip-permissions \
	--system-prompt-file "${REPO_DIR}/sys_prompt/alan-default-next.md" \
	"$@"

# exec claude --dangerously-skip-permissions "$@"

# exec claude
