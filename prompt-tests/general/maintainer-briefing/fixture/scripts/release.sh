#!/usr/bin/env bash
set -euo pipefail

NEW="${1:?usage: release.sh X.Y.Z}"

test -z "$(git status --porcelain)" || { echo "working tree is dirty" >&2; exit 1; }

CUR="$(grep -m1 '^version = ' pyproject.toml | cut -d'"' -f2)"
echo "$CUR -> $NEW"
sed -i "s/^version = \"$CUR\"/version = \"$NEW\"/" pyproject.toml

python -m pytest -q

git add pyproject.toml CHANGELOG.md
git commit -m "release $NEW"
git tag -a "v$NEW" -m "v$NEW"
git push origin HEAD "v$NEW"
