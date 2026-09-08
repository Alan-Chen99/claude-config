# payments-relay runbook

Forwards settlement records from the ledger service to the vendor's ingest API.
Older alerts call it `ledger-forwarder` — same service.

## Deploy

`./deploy.sh <env>` rolls one pod at a time, ~4 min in prod. Watch with
`kubectl rollout status deploy/relay`; `rollout pause` is safe.

Migrations are separate — run `./migrate.sh` yourself. **Order matters**:

- **Adding a column: before the restart.** New code writes it on boot and
  crash-loops without it.
- **Dropping or renaming: after the roll finishes.** Old pods still use the old
  name and 500 until they're replaced.

Avoid Friday deploys unless billing is around — reconciliation runs Saturday.

## Config

Env vars, read once at boot — any change needs a restart.

- `WORKERS=4` — **a ceiling, not a tuning knob.** The vendor allows 5
  connections per tenant and the admin console holds one. Above 4 you get
  `pool exhausted`, reaching us as an undifferentiated 503.
- `LOG_LEVEL=info` — debug is one line per record and the pipeline drops above
  ~2000 lines/sec, so debug in prod can lose the lines you wanted.
- `BATCH_SIZE=200` (vendor max), `RETRY_BACKOFF=2s`, `SHUTDOWN_GRACE=30`.

## Troubleshooting

- **503s from the vendor** — check `WORKERS` first; it explains this more than
  everything else combined.
- **Stuck in `pending` over an hour** — a lost acknowledgement, not a lost
  record. Re-driving is safe: `./redrive.sh <record-id>`, **one id at a time.
  Never loop it** — 900 records looped once rate-limited the tenant for an hour.
- **Worker won't start** — read the first line of the crash output. Usually a
  missing env var (it names it), sometimes an unrun migration (a column error).
- **Alerts with no traffic** — the synthetic check fires on vendor downtime
  alone. Check the vendor status page before paging.

## Everything else

- **No staging** — production and your laptop, and finance turned down a second
  vendor tenant.
- **Prod access**: bastion, request in #platform-access. 8 hours, no auto-renew.
- **Reconciliation** runs Sat 04:00; tickets go to billing's queue, not ours.
- **Conventions** are in `CONTRIBUTING.md` — read §4 before force-pushing.
