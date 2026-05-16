#!/usr/bin/env bash

set -eux

export GIT_AUTHOR_NAME="Claude(Ralph)"
export GIT_AUTHOR_EMAIL="81847+claude@users.noreply.github.com"
export GIT_COMMITTER_NAME="$GIT_AUTHOR_NAME"
export GIT_COMMITTER_EMAIL="$GIT_AUTHOR_EMAIL"

export IS_SANDBOX=1

unset DISPLAY

exec ralph run --no-auto-commit -c /workspace/ralph/build.yml "$@"
