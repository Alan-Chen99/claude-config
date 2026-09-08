# payments-relay runbook

Forwards settlement records from the ledger to the vendor's ingest API. Older
alerts say `ledger-forwarder`; same service.

## Troubleshooting

**503s from the vendor.** Almost always `pool exhausted`, reaching us as a bare
503. Check `WORKERS` first.

**Records stuck in `pending` over an hour.** A lost acknowledgement, not a lost
record; re-driving is safe. `./redrive.sh <record-id>`, one id at a time — never
in a loop, which once rate-limited the tenant for an hour.

**Worker will not start.** Read the first line of the crash output: usually a
missing env var (it names it), or an unrun migration — a column error on boot.

**Alerts with no traffic.** The synthetic check fires whenever the vendor is
down. Check their status page before paging.

## Deploying

`./deploy.sh <env>` rolls one pod at a time, ~4 min in production. Watch
`kubectl rollout status deploy/relay`; `kubectl rollout pause` is safe to sit in.

Migrations are separate (`./migrate.sh`) and order matters:

- **Add a column: before the restart.** New code writes to it on boot and
  crash-loops without it.
- **Drop or rename: after the roll.** Old pods reference the old name and 500
  until replaced.

## Configuration

Env vars, read once at boot; changes need a restart.

- `WORKERS=4` — a hard ceiling, not a tuning knob: the vendor allows five
  connections per tenant and the admin console holds one permanently.
- `LOG_LEVEL=info` — debug logs every record and the pipeline drops above ~2000
  lines/sec, so debug in production loses the lines you wanted.
- `BATCH_SIZE=200` (vendor max), `RETRY_BACKOFF=2s`, `STRICT_ORDERING=0`,
  `SHUTDOWN_GRACE=30` (seconds for in-flight sends).

## Operating notes

- **No staging** — production and your laptop; finance declined a second tenant.
- **Reconciliation** runs Saturday 04:00; tickets go to billing's queue, not
  ours. Avoid Friday deploys. It has not yet seen a month-end close, when the
  ledger backdates entries — treat a first month-end discrepancy as unproven.
- **Prod access:** bastion; ask in #platform-access. Eight hours, no auto-renew.
- **Rebasing:** read `CONTRIBUTING.md` section 4 first.
