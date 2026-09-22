#!/usr/bin/env bash
# Mechanical half of a deploy. The judgement half is in docs/deploy.md.
set -euo pipefail

ENV="${1:?usage: deploy.sh --env <staging|prod>}"

git pull --ff-only
make test
make migrate
aws s3 sync build/ "s3://ingest-api-artifacts/" --delete
make deploy
curl -sf "https://ingest-api.internal/healthz"
echo "deployed to $ENV; post the release tag in #ingest-deploys"
