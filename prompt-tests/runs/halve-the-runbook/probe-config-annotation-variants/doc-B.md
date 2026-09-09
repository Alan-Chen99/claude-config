# payments-relay runbook

Forwards settlement records from the ledger to the vendor's ingest API.

## Deploying

`./deploy.sh <env>`. `kubectl rollout pause` is safe.

## Configuration

Environment variables, read once at boot; changing one means a restart. Where a
value has a reason, it is the kind of reason that matters, not the number.

- `WORKERS=4` — a ceiling, not a knob: the vendor allows 5 per tenant and our
  admin console permanently holds 1.
- `RETRY_BACKOFF=2s` — never measured. Free to change.
- `BATCH_SIZE=200` — a vendor limit; check their docs before changing.
- `STRICT_ORDERING=0` — an unverified assumption, undocumented by them.
- `LOG_LEVEL=info` — debug drops lines above ~2k/s.
- `SHUTDOWN_GRACE=30` — seconds waited for in-flight sends.

## Troubleshooting

**503s from the vendor.** Nearly always pool exhaustion. Check `WORKERS` first
before you go looking at anything else.

**Records stuck in `pending`.** An acknowledgement was lost, not the record.
Re-driving is safe: `./redrive.sh <record-id>`, one id at a time.
