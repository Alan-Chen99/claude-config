#!/usr/bin/env bash
# Stamp the release version onto the build.
set -euo pipefail

VERSION="$(git describe --tags --abbrev=0)"
echo "building ${VERSION}"

docker build -t "ghcr.io/acme/release-bot:${VERSION}" .
git tag -a "${VERSION}" -m "release ${VERSION}"
git push origin "${VERSION}"
