# payments-relay runbook

Forwards settlement records from the ledger to the vendor's ingest API. Older
alerts call it `ledger-forwarder`; same service.

## Deploying

`./deploy.sh <env>` rolls one pod at a time, ~4 min in prod. Watch with
`kubectl rollout status deploy/relay`; `rollout pause` is safe.

Migrations are separate (`./migrate.sh`); order matters: **add** a column
*before* the restart (new code writes to it on boot, else crash-loop); **drop or
rename** *after* the roll (old pods still use the old name and 500 until
replaced).

Avoid Friday deploys without billing around; reconciliation runs Saturday.

## Configuration

Env vars, read once at boot; changes need a restart.

- `WORKERS=4` — a ceiling, not a tuning choice: the vendor allows five
  connections per tenant and the admin console holds one permanently. Higher
  gives `pool exhausted`.
- `BATCH_SIZE=200` — the vendor's documented maximum.
- `LOG_LEVEL=info` — debug is one line per record; the pipeline drops above
  ~2000 lines/sec, so it can lose the lines you wanted.
- `RETRY_BACKOFF=2s` — never measured; the place to start if retries need work.

## Troubleshooting

- **503s.** Nearly always pool exhaustion; check `WORKERS` first.
- **Stuck in `pending` over an hour.** A lost acknowledgement, not a lost
  record; `./redrive.sh <record-id>` is safe. Never loop it — ~900 in a loop
  rate-limited the tenant for an hour; threshold unknown.
- **Worker won't start.** Usually a missing env var, named in the first line of
  the crash output. Otherwise an unrun migration: a column error on first query.
- **Alerts with no traffic.** The synthetic check fires on vendor outages even
  when we're sending nothing — check their status page before paging.

## Operating notes

- Reconciliation: 04:00 Saturday, one ticket per discrepancy into billing's
  queue, not ours. No false positives yet, but never through a month-end close —
  the ledger backdates into reported periods, so treat a first month-end
  discrepancy as unproven.
- No staging: production and your laptop. The vendor bills per tenant; finance
  declined a second in March — ask first.
- Bastion access: request in #platform-access, eight hours, no auto-renew.
- `CONTRIBUTING.md` governs repo conventions; read section 4 before rebasing
  anything already pushed.

History, `shipit`, the remaining env vars, and local setup: `RUNBOOK-full.md`.
