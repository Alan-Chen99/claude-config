#!/usr/bin/env bash

set -eux

# The launcher's version, recorded with the rest of the environment by
# `agent-tools hook-provenance` (the CLAUDE prefix). Bump it, and add its line
# here, when a change alters the configuration a session launched from here
# starts with -- a variable set or dropped, a value or its meaning, an argument
# to claude. A change that starts every session the same way does not. A reader
# branches on this, not on which variables happen to be present.
#   1  first versioned: the configuration below
#   2  --plugin-dir scripts/cache-keepalive when stdin is a terminal
export CLAUDE_SH_VERSION=2

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

# cc roots its scratchpad at CLAUDE_CODE_TMPDIR (Ap(), chunk-v4kbwz0z.js:300),
# for the main agent and for subagents alike, so redirecting it here is the only
# way both get one directory. The root follows $HOME rather than naming /tmp,
# because /tmp is container overlay and is lost on a rebuild while this
# container's home is a host bind mount.
# The same variable also roots plugin dirs, skill zips and the IPC socket dir;
# cc falls back to /tmp for the socket when the path is too long (Sgi(),
# chunk-k4sr74rj.js:545, found by "cc-socks").
export CLAUDE_CODE_TMPDIR="$HOME/.claude/tmp"

# readlink -f resolves the ~/.local/bin/claude.sh symlink, so the prompt loaded
# belongs to the checkout the script physically lives in: the canonical repo via
# the installed symlink, or a worktree's own prompt when that copy is run by path.
CLAUDE_SH_SELF="$(readlink -f "${BASH_SOURCE[0]}")"
REPO_DIR="$(cd "$(dirname "$CLAUDE_SH_SELF")/.." && pwd)"

# The chain of launchers that configured this session, in order, appended by
# each one it passes through. `agent-tools hook-provenance` records it into the
# transcript; nothing else can recover it, because the `exec` below replaces
# this shell and leaves no process to walk back to. Assigned before the export
# so a failed `readlink` is not masked by `export`'s own exit status, which
# would hand the chain a truncated entry under `set -e`.
export CLAUDE_SH_LAUNCHERS="${CLAUDE_SH_LAUNCHERS:+$CLAUDE_SH_LAUNCHERS:}$CLAUDE_SH_SELF"

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
	echo "claude.sh: WARNING: nothing listening on ${PROXY_HOST}:${PROXY_PORT}; HTTPS_PROXY unset, requests are NOT intercepted. Start it with: systemctl --user start claude-intercept.service, or without a user manager: ${HOME}/.claude/venvs/claude-config/bin/python ${REPO_DIR}/scripts/intercept/run-proxy.py" >&2
fi

# One randomized draw per interactive session for the total_tokens reminder,
# against the hypothesis that the marker changes how a long session ends up.
# A fixture cannot answer that: a single-turn case measures the response to the
# number, not what that response costs over several hundred thousand tokens and
# several compactions, and on a single-turn case both arms reached the same
# answer, so the outcome measure was at ceiling.
#
# Both arms are safe to draw on real work. `padded-countdown` is what ships, and
# the two were indistinguishable on every measure that had room to move
# (notes/total-tokens-reminder.md). The harmful regime is a *small* budget, which
# neither arm sets.
#
# `-t 0` confines the draw to interactive sessions. scripts/prompt-test-cc.sh
# reaches claude through this launcher with stdin on a file, so without the test
# every prompt-test case would silently acquire a randomized env var.
#
# padded-countdown is named rather than left unset so a GrowthBook flip cannot
# redefine the treatment arm mid-trial (Ndn(), src/chunk-j0tbz6ra.js:90236, found
# by tengu_lapis_anchor).
#
# The draw is untraced because `set -x` would otherwise print the arm to the
# terminal at every session start, and one candidate outcome is how often the
# user redirects the session. Blinding is impossible -- the marker is in the
# context -- but an arm announced in the first line of scrollback is worse. The
# guard below still traces a value the caller supplied: that is the caller's own
# value, and such a session is out of the trial anyway.
#
# Three readings label a session, each answering a different question. cc's
# `attachment` records carry the marker: what was *delivered*, and an `off` session
# leaves none. `agent-tools hook-provenance` snapshots the environment into the
# transcript: what was *configured*. Neither can say whether this launcher drew
# that configuration or inherited it, because the snapshot is taken after the
# `exec` below, where a drawn value and a caller's value are the same variable --
# CLAUDE_SH_TOKENS_REMINDER_SOURCE is that third reading. It is set on every path,
# so its absence is a launcher older than it rather than a session nobody drew for,
# and it reaches the record through the `CLAUDE` prefix in hook_provenance.rs,
# pinned there by a test rather than by a name in the recording code.
# Protocol, candidate outcomes and invalidation conditions:
# docs/total-tokens-reminder-trial.md
if [ -n "${CLAUDE_CODE_TOTAL_TOKENS_REMINDER:-}" ]; then
	export CLAUDE_SH_TOKENS_REMINDER_SOURCE=caller
elif [ ! -t 0 ]; then
	export CLAUDE_SH_TOKENS_REMINDER_SOURCE=skipped-not-interactive
else
	set +x
	if [ $((RANDOM % 2)) -eq 0 ]; then
		export CLAUDE_CODE_TOTAL_TOKENS_REMINDER=off
	else
		export CLAUDE_CODE_TOTAL_TOKENS_REMINDER=padded-countdown
	fi
	set -x
	export CLAUDE_SH_TOKENS_REMINDER_SOURCE=draw
fi

# The cache keepalive mod (scripts/cache-keepalive/README.md) shares the draw's
# `-t 0` test: prompt-test runs reach claude through here with stdin on a file
# and stay at "no plugins loaded".
PLUGIN_ARGS=()
if [ -t 0 ]; then
	PLUGIN_ARGS=(--plugin-dir "${REPO_DIR}/scripts/cache-keepalive")
fi

exec claude --dangerously-skip-permissions \
	--system-prompt-file "${REPO_DIR}/sys_prompt/alan-default-next.md" \
	"${PLUGIN_ARGS[@]}" \
	"$@"

# exec claude --dangerously-skip-permissions "$@"

# exec claude
