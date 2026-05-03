#!/usr/bin/env bash

set -eux

export GIT_AUTHOR_NAME="Claude"
export GIT_AUTHOR_EMAIL="81847+claude@users.noreply.github.com"
export GIT_COMMITTER_NAME="$GIT_AUTHOR_NAME"
export GIT_COMMITTER_EMAIL="$GIT_AUTHOR_EMAIL"

export IS_SANDBOX=1

export NODE_OPTIONS='--require /home/chenxy/repos/claude-config/docs/system-prompt-snapshot/intercept.js'

export BASH_DEFAULT_TIMEOUT_MS=10000
export BASH_MAX_TIMEOUT_MS=30000

exec claude --dangerously-skip-permissions "$@"
# exec claude "$@"

# exec npx @anthropic-ai/claude-code@2.0.14 --dangerously-skip-permissions --system-prompt-file /repos/claude-config/SYSTEM.md "$@"

# exec claude
