#!/usr/bin/env bash
# Push every built image to the registry, then sign the manifest.
set -euo pipefail

VERSION="${1:?usage: push.sh <version>}"

for arch in amd64 arm64; do
  docker push "ghcr.io/acme/release-bot:${VERSION}-${arch}"
done

docker manifest create "ghcr.io/acme/release-bot:${VERSION}" \
  "ghcr.io/acme/release-bot:${VERSION}-amd64" \
  "ghcr.io/acme/release-bot:${VERSION}-arm64"
docker manifest push "ghcr.io/acme/release-bot:${VERSION}"

cosign sign --key "${COSIGN_KEY}" "ghcr.io/acme/release-bot:${VERSION}"
