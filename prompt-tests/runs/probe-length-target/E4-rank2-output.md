# payments-relay runbook

Forwards settlement records from the ledger to the vendor's ingest API. Older
alerts and dashboards call it `ledger-forwarder`; same service.

## Deploying

`./deploy.sh <env>` rolls one pod at a time, ~4 min in prod; watch with
`kubectl rollout status deploy/relay`. `rollout pause` is safe. Using this over
the platform team's `shipit` pipeline is deliberate — switching is a
conversation, not a unilateral change.

Migrations are separate (`./migrate.sh`) and order matters: **add** a column
*before* the restart (new code writes it on boot, else crash-loop); **drop or
rename** *after* the roll (old pods 500 on the old name until replaced).

Reconciliation runs Saturday, so a bad Friday deploy gets found by a customer —
avoid one unless billing is around. Nobody enforces this; it is not a rule.

## Configuration

Env vars, read once at boot; changes need a restart.

- `WORKERS=4` — a ceiling, not a tuning choice: the vendor allows five
  connections per tenant, one held permanently by the admin console. Higher
  gives `pool exhausted`, reaching us as an undifferentiated 503.
- `BATCH_SIZE=200` — the vendor's documented maximum.
- `LOG_LEVEL=info` — debug is one line per record and the pipeline drops above
  ~2000 lines/sec, so debug in prod can lose the lines you wanted.
- `RETRY_BACKOFF=2s` — first value anyone typed, never measured. A fine
  starting point *if* retry behaviour needs work.
- `STRICT_ORDERING=0` — we assume the vendor preserves send order; never
  confirmed with them, never documented. Nothing depends on it yet.

## Troubleshooting

- **503s.** Nearly always pool exhaustion; check `WORKERS` first.
- **Stuck in `pending` over an hour.** A lost acknowledgement, not a lost
  record; `./redrive.sh <record-id>` is safe. Never loop it — 900 records in a
  loop rate-limited the tenant for an hour; threshold unknown.
- **Worker won't start.** Usually a missing env var — named in the first line
  of the crash output. Otherwise an unrun migration: a column error on first
  query.
- **Alerts with no traffic.** The synthetic check alerts when the vendor is down
  even if we're sending nothing. Check their status page before paging.

## Operating notes

- Reconciliation: 04:00 Saturday, one ticket per discrepancy into billing's
  queue. No false positives in eleven weeks, but never through a month-end
  close — the ledger backdates into already-reported periods, so treat a first
  month-end discrepancy as unproven.
- Production and your laptop; no staging. The vendor bills per tenant and
  finance declined a second in March — ask before assuming.
- Bastion access: request in #platform-access, eight hours, no auto-renew.
- `CONTRIBUTING.md` governs conventions; read section 4 before you force-push.
- Local dev setup: `RUNBOOK-full.md`.
