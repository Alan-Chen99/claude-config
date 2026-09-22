#!/usr/bin/env bash
# Push pending records to the vendor's ingest endpoint.
set -euo pipefail

BATCH=200
ENDPOINT="https://api.vendor.example/v2/ingest"

pending() { find ./queue -name '*.json' -print0; }

pending | xargs -0 -n "$BATCH" -- python3 ./pack.py \
  | while read -r payload; do
      curl -sS -f -X POST "$ENDPOINT" \
        -H "Authorization: Bearer ${VENDOR_TOKEN:?VENDOR_TOKEN unset}" \
        -H 'Content-Type: application/json' \
        --data-binary "@$payload"
    done
