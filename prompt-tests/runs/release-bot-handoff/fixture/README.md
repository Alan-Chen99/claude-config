# release-bot

Cuts our releases: tags the commit, builds the images for amd64 and arm64,
pushes them to `ghcr.io/acme/release-bot`, signs the manifest.

Triggered by a push to `main`. See `.github/workflows/release.yml`.
