# payments-relay runbook

Forwards settlement records from the ledger to the vendor's ingest API.

## Deploying

`./deploy.sh <env>`. `kubectl rollout pause` is safe.

## Configuration

Environment variables, read once at boot; changing one means a restart.

`WORKERS=4`, `RETRY_BACKOFF=2s`, `BATCH_SIZE=200`, `STRICT_ORDERING=0`,
`LOG_LEVEL=info`, `SHUTDOWN_GRACE=30`.

This document does not record why any of these values are what they are, or
whether any of them can be changed.

## Troubleshooting

**503s from the vendor.** Nearly always pool exhaustion. Check `WORKERS` first
before you go looking at anything else.

**Records stuck in `pending`.** An acknowledgement was lost, not the record.
Re-driving is safe: `./redrive.sh <record-id>`, one id at a time.
