# payments-relay runbook

Forwards settlement records from the ledger service to the vendor's ingest API.
Older alerts call it `ledger-forwarder` — same service.

## Troubleshooting

**503s from the vendor.** Nearly always pool exhaustion. Check `WORKERS` first —
it explains this more often than every other cause put together.

**Records stuck in `pending`.** `pending` means handed to the vendor, `sent`
means acknowledged. Stuck over an hour means a lost acknowledgement, not a lost
record. Re-driving is safe: `./redrive.sh <record-id>`, one id at a time by
design.

**Worker will not start.** Usually a missing environment variable, and the error
names it — read the first line of the crash output. Next most common is an unrun
migration, which surfaces as a column error in the first query on boot.

**Alerts firing with no traffic.** The synthetic check hits a fixed record id
every minute and alerts on its own if the vendor is down. Check the vendor
status page before paging anyone.

## Deploying

`./deploy.sh <env>` builds, pushes, and rolls one pod at a time — about four
minutes in production. Watch with `kubectl rollout status deploy/relay`.
`kubectl rollout pause` is safe; nothing times out on a paused roll. We use this
script rather than the platform team's `shipit` pipeline; moving it is a
conversation to have, not a change to just make.

Migrations are separate. Run `./migrate.sh` yourself; order matters:

- **Adding a column** — before the restart; new code writes to it on boot and
  crash-loops without it.
- **Dropping or renaming** — after the rollout; not-yet-replaced pods still
  reference the old name and 500 until it finishes.

Not a rule, but reconciliation runs Saturday morning, so a bad Friday deploy
gets found by a customer. Avoid Fridays unless billing is around.

## Configuration

Environment variables, read once at boot. No reload mechanism — changing any of
these means a restart.

| Variable | Default | Notes |
| --- | --- | --- |
| `WORKERS` | `4` | A ceiling, not a tuning choice: the vendor allows five connections per tenant and the admin console permanently holds one. Above four, `pool exhausted` surfaces as a generic 503. |
| `BATCH_SIZE` | `200` | The vendor's documented maximum. |
| `RETRY_BACKOFF` | `2s` | The first value anyone typed; never measured. Fine place to start if retry behaviour needs work. |
| `STRICT_ORDERING` | `0` | We assume the vendor preserves send order within a batch, but have never confirmed it with them. Nothing today depends on the answer. |
| `LOG_LEVEL` | `info` | Debug is one line per record; the pipeline drops above ~2000 lines/sec, so debug in production can lose the lines you wanted. |
| `SHUTDOWN_GRACE` | `30` | Seconds to wait for in-flight sends before exiting. |

## Access

Production access is through the bastion. Request it in #platform-access: eight
hours at a time, no auto-renew.

`CONTRIBUTING.md` governs repository conventions; read section 4, on
force-pushing, before rebasing anything already pushed.

**Never run `./redrive.sh` in a loop.** In February someone redrove ~900 records
in a shell loop and the vendor rate-limited the whole tenant for an hour. The
actual threshold is unknown.

## Reconciliation job

Runs 04:00 Saturday, compares what we sent against what the vendor acknowledges,
and opens one ticket per discrepancy. Tickets go to the billing queue, not ours;
billing triages them Monday.

No false positives in eleven weeks, but it has not seen a month-end close — when
the ledger backdates entries into an already-reported period. Treat a first
month-end discrepancy as unproven.

## Environments

Production and your laptop; no staging. The vendor bills per tenant and finance
turned down a second one in March, so ask before assuming one can be spun up.

## Appendix: local setup

Python 3.11+ (`brew install python@3.11`, or
`apt install python3.11 python3.11-venv`), then from the repository root:

```
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
pytest -q          # ~90 seconds
```

`pytest` not finding the package almost always means the virtualenv is not
activated. `docker-compose.yml` brings up a Postgres on 5433 that only the tests
use.
