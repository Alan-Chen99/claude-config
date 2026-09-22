#!/usr/bin/env bash
# The case measures an edit to an existing document, so the document needs a
# committed baseline for the diff to be read against.
set -euo pipefail
git init -q .
git add -A
git -c user.email=dev@example.com -c user.name=dev commit -qm "ingest-api deploy docs"
