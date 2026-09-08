# payments-relay runbook

Forwards settlement records from the ledger service to the vendor's ingest API.
Older alerts name it `ledger-forwarder` — same service.

## Deploying

`./deploy.sh <env>` rolls one pod at a time; ~4 min in production.
`kubectl rollout status deploy/relay` to watch, `kubectl rollout pause` is safe.

Migrations are separate (`./migrate.sh`); order matters:

- **Adding a column:** before the restart, or new code crash-loops on boot.
- **Dropping or renaming:** after the rollout, or old pods 500 until replaced.

## Configuration

Read at boot only; changes need a restart.

| Variable | Default | Notes |
| --- | --- | --- |
| `WORKERS` | 4 | Ceiling: vendor allows 5 per tenant, admin console holds 1. |
| `BATCH_SIZE` | 200 | Vendor maximum. |
| `RETRY_BACKOFF` | 2s | |
| `STRICT_ORDERING` | 0 | |
| `LOG_LEVEL` | info | Debug is a line per record; pipeline drops above ~2000/s. |
| `SHUTDOWN_GRACE` | 30 | Seconds for in-flight sends. |

## Troubleshooting

**503s from the vendor.** Check `WORKERS` first — pool exhaustion outweighs all
other causes.

**Records stuck in `pending`.** Past an hour the acknowledgement was lost, not
the record. Redriving is safe: `./redrive.sh <record-id>`, one id at a time —
never a loop, which rate-limits the whole tenant.

**Worker will not start.** Usually a missing environment variable, named in the
crash output's first line; otherwise an unrun migration, seen as a column error.

**Alerts with no traffic.** The synthetic check fires on vendor downtime alone —
check their status page first.

## Operations

**Reconciliation** runs Saturday 04:00, filing one ticket per discrepancy into
billing's queue, not ours — so avoid Friday deploys unless billing is around.
Its first month-end close is untested: the ledger backdates into reported
periods, so treat those tickets as unproven.

**Environments:** production and your laptop. No staging — the vendor bills per
tenant and finance declined a second in March.

**Access:** via the bastion, requested in #platform-access. Eight hours, no
auto-renew.

**Conventions:** `CONTRIBUTING.md` governs; read section 4 before force-pushing.

## Local setup

Python 3.11+ in a venv, `pip install -r requirements-dev.txt`, `pytest -q`
(~90s). Import errors mean the venv is not active. `docker-compose.yml` runs
test Postgres on 5433.
