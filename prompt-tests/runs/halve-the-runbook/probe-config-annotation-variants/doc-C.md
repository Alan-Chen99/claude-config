# payments-relay runbook

Forwards settlement records from the ledger to the vendor's ingest API.

## Deploying

`./deploy.sh <env>`. `kubectl rollout pause` is safe.

## Configuration

Environment variables, read once at boot; changing one means a restart.

- `WORKERS=4` — a ceiling, not a tuning choice: the vendor's pool is 5 per
  tenant and the admin console holds 1. Above it, `pool exhausted` reaches us as
  an undifferentiated 503.
- `RETRY_BACKOFF=2s` — the first value anyone typed, never measured; a fine
  place to start.
- `BATCH_SIZE=200` — the vendor's documented maximum.
- `STRICT_ORDERING=0` — we think they ingest in send order, from their
  acknowledgements alone; never put to them, never documented by them, and
  nothing today depends on it.
- `LOG_LEVEL=info` — debug is one line per record and the pipeline drops above
  ~2,000 lines/s, so debug in production can lose the lines you turned it on for.
- `SHUTDOWN_GRACE=30` — seconds waited for in-flight sends.

## Troubleshooting

**503s from the vendor.** Nearly always pool exhaustion. Check `WORKERS` first
before you go looking at anything else.

**Records stuck in `pending`.** An acknowledgement was lost, not the record.
Re-driving is safe: `./redrive.sh <record-id>`, one id at a time.
