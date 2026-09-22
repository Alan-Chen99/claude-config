#!/usr/bin/env bash
# The measurement is a diff against the document as it stood, so the document
# needs a committed baseline.
set -euo pipefail
git init -q .
git add -A
git -c user.email=dev@example.com -c user.name=dev commit -qm "notify"
