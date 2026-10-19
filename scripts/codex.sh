#!/usr/bin/env bash
set -euo pipefail

# Pin both identities, including when launched inside a Claude session.
export GIT_AUTHOR_NAME="Codex"
export GIT_AUTHOR_EMAIL="81847+claude@users.noreply.github.com"
export GIT_COMMITTER_NAME="$GIT_AUTHOR_NAME"
export GIT_COMMITTER_EMAIL="$GIT_AUTHOR_EMAIL"

exec codex "$@"
