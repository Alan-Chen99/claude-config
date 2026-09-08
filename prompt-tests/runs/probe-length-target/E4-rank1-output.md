# payments-relay runbook

Forwards settlement records from the ledger to the vendor's ingest API. Older
alerts call it `ledger-forwarder`; same service.

## Deploying

`./deploy.sh <env>` rolls one pod at a time, ~4 min in prod. Watch with
`kubectl rollout status deploy/relay`; pausing mid-roll is safe.

Not the platform team's `shipit` pipeline — deliberate, not drift; both worked.
Moving it is a conversation, not a change.

Migrations are separate (`./migrate.sh`). **Add** a column *before* the restart
(new code writes it on boot, else crash-loop); **drop or rename** *after* the
roll (old pods 500 on the old name until replaced).

Avoid Friday deploys without billing around — not a rule, but reconciliation
runs Saturday and customers find the bug first.

## Configuration

Env vars, read once at boot; changes need a restart. The ones that matter:

- `WORKERS=4` — a ceiling, not a tuning choice: the vendor allows five
  connections per tenant and the admin console permanently holds one. Higher
  gives `pool exhausted`.
- `BATCH_SIZE=200` — the vendor's documented maximum.
- `LOG_LEVEL=info` — debug is one line per record; the pipeline drops above
  ~2000 lines/sec, so debug in prod can lose the lines you wanted.
- `RETRY_BACKOFF=2s` — never measured; start here if retries need work.
- `STRICT_ORDERING=0` — we assume the vendor ingests in order; never asked,
  never documented. Nothing depends on it today.

## Troubleshooting

- **503s.** Nearly always pool exhaustion; check `WORKERS` first.
- **Stuck in `pending` over an hour.** A lost ack, not a lost record;
  `./redrive.sh <record-id>` is safe. Never loop it — 900 in a loop rate-limited
  the tenant for an hour; threshold unknown.
- **Worker won't start.** A missing env var (named in the crash output) or an
  unrun migration (column error on first query).
- **Alerts, no traffic.** The synthetic check fires when the vendor is down.
  Check their status page before paging.

## Operating notes

- Reconciliation: 04:00 Saturday, one ticket per discrepancy to billing's queue.
  Clean for eleven weeks but never through a month-end close — the ledger
  backdates into reported periods, so treat a first month-end discrepancy as
  unproven.
- Production and your laptop; no staging. Vendor bills per tenant; finance
  declined a second in March — ask before assuming.
- Bastion access: request in #platform-access, eight hours, no auto-renew.
- `CONTRIBUTING.md` governs repo conventions; read section 4 (force-pushing)
  before rebasing anything pushed.
