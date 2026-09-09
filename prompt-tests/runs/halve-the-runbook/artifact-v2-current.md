# payments-relay runbook

Forwards settlement records from the ledger service to the vendor's ingest API.
Some old alerts still fire as `ledger-forwarder`, and several source modules
match neither name; it is all one service.

## Deploying

`./deploy.sh <env>` builds, pushes, and rolls one pod at a time — about four
minutes in production. Watch it with `kubectl rollout status deploy/relay`.
`kubectl rollout pause` is safe; paused is a normal state and nothing times out
on it. We use it over the platform team's `shipit` pipeline because the team
already knew it, not because `shipit` failed; moving is a conversation, not a
unilateral change.

**Migrations are not part of the deploy.** Run `./migrate.sh` yourself; the
order depends on the migration.

- **Adds a column — before the restart.** New code writes to it on boot and
  crash-loops without it.
- **Drops or renames a column — after the roll finishes.** Not-yet-replaced pods
  still reference the old name and 500 until they are gone.

Try not to deploy on a Friday unless billing is around. Not a rule, but the
Saturday reconciliation means a bad one gets found by a customer instead of us.

## Configuration

Environment variables, read once at boot; no reload, so any change means a
restart.

- `WORKERS=4` — a ceiling, not a tuning choice: the vendor allows five
  concurrent connections per tenant, and the admin console permanently holds
  one. Above four you get `pool exhausted`, which reaches us as a bare 503.
- `BATCH_SIZE=200` — the vendor's documented maximum.
- `RETRY_BACKOFF=2s` — the first value anyone typed, never measured; a fine
  place to start if retry behaviour needs work.
- `STRICT_ORDERING=0` — we assume the vendor preserves order within a batch,
  from their acknowledgements alone; never confirmed. Nothing we run today
  depends on it.
- `LOG_LEVEL=info` — debug is one line per record and the pipeline drops above
  ~2000 lines/sec, so debug in production can lose the lines you turned it on to
  see.
- `SHUTDOWN_GRACE=30` — seconds to wait for in-flight sends before exiting.

## Troubleshooting

**503s from the vendor.** Nearly always pool exhaustion — check `WORKERS` before
anything else.

**Records stuck in `pending`.** `pending` means handed to the vendor, `sent`
means acknowledged. Over an hour in `pending` is a lost acknowledgement, not a
lost record, so re-driving is safe: `./redrive.sh <record-id>`, one id at a time
by design. **Never loop it**: one February incident, about nine hundred
redrives in a shell loop, rate-limited the whole tenant for an hour. It has not
recurred, and nobody has found the real threshold.

**The worker will not start.** Nine times out of ten a missing environment
variable, and the error message names it — read the first line of the crash
output before anything else. Next most common is an unrun migration, showing as
a column error in the worker's first query.

**Alerts firing with no traffic.** The synthetic check hits a fixed record id
every minute and alerts on its own if the vendor is down, even when we send
nothing. Check the vendor status page before paging anyone.

## Reconciliation

Runs 04:00 Saturday, compares sent against acknowledged, and opens one ticket
per discrepancy into the **billing** queue, not ours; billing triages Monday.

No false positives in the eleven weeks since deploy — but it has not yet run
through a month-end close, when the ledger backdates entries into a period we
have already reported. Treat a first month-end discrepancy as unproven.

## Access and environments

Production and your laptop; **no staging**. Not an oversight awaiting a fix: the
vendor bills per tenant and finance turned down a second tenant in March — ask
them before assuming one can be spun up.

Production access is through the bastion: request in #platform-access, eight
hours at a time, no auto-renew.

`CONTRIBUTING.md` governs branch naming, commit format, and review. Section 4,
on force-pushing, is the one that catches people out — read it before rebasing
anything already pushed.

## Appendix: local setup

Python 3.11+, virtualenv, `pip install -r requirements-dev.txt`, `pytest -q`
(~90s). `pytest` not finding the package means an unactivated virtualenv — by far
the most common setup problem. `docker-compose.yml` runs Postgres on 5433, tests
only.
