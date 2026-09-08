# payments-relay runbook

Forwards settlement records from the ledger to the vendor's ingest API.

The service predates its current name and not everything was renamed with it:
older alerts still fire under `ledger-forwarder`, several source module names
match nothing in this document, and the oldest dashboards carry two entries for
what is one service. None of it is a second service.

## Deploying

`./deploy.sh <env>` builds the image, pushes it, and rolls one pod at a time —
about four minutes in prod. Watch it with `kubectl rollout status deploy/relay`.
`kubectl rollout pause` is safe to leave sitting: paused is a normal state and
nothing times out on it.

Deploys go through that script rather than the platform team's `shipit`
pipeline. Both ran in parallel through most of 2024 and both worked; the script
stayed because the team already knew it, not because `shipit` ever failed.
Moving it is a conversation to have, not a change to just make.

Migrations are separate (`./migrate.sh`) and order matters: **add** a column
*before* the restart (new code writes to it on boot, else crash-loop); **drop or
rename** *after* the roll (old pods still use the old name and 500 until
replaced).

Avoid Friday deploys without someone from billing around. Nobody enforces this
and it is not a rule — but reconciliation runs Saturday morning, and a bad
Friday deploy tends to get found by a customer instead of by us.

## Configuration

Env vars, read once at boot. There is no reload mechanism, so any change means a
restart. All six:

- `WORKERS=4` — a ceiling, not a tuning choice: the vendor allows five
  connections per tenant and the admin console permanently holds one. Higher
  gives `pool exhausted`, which reaches us as an undifferentiated 503.
- `BATCH_SIZE=200` — the vendor's documented maximum.
- `LOG_LEVEL=info` — debug is one line per record; the pipeline drops above
  ~2000 lines/sec, so debug in prod can lose the lines you turned it on to see.
- `SHUTDOWN_GRACE=30` — seconds the worker waits for in-flight sends before
  exiting.
- `RETRY_BACKOFF=2s` — the first value anyone typed, never measured against
  anything. The place to start if retry behaviour ever needs work.
- `STRICT_ORDERING=0` — the vendor's acknowledgements have always looked like
  they ingest a batch in the order we send it, but they have never documented it
  and nobody has put the question to them. Nothing we run today depends on the
  answer.

## Troubleshooting

- **503s.** Nearly always pool exhaustion; check `WORKERS` before looking at
  anything else. It explains this symptom more often than every other cause put
  together.
- **Stuck in `pending` over an hour.** The worker marks a record `pending` when
  it hands it to the vendor and `sent` when the vendor acknowledges, so a long
  `pending` is a lost acknowledgement, not a lost record. Re-driving is safe:
  `./redrive.sh <record-id>`, one id at a time by design. Never loop it. Nine
  hundred records redriven in a shell loop rate-limited the whole tenant for an
  hour, and nobody has worked out where the actual threshold is.
- **Worker won't start.** Usually a missing env var, named in the first line of
  the crash output — read that before doing anything else. Otherwise an unrun
  migration, which looks like a column error on the first query the worker makes
  on boot.
- **Alerts with no traffic.** The synthetic check runs every minute against a
  fixed record id and alerts on its own when the vendor is down, even when we're
  sending nothing. Check their status page before paging anyone.

## Operating notes

- **Reconciliation.** 04:00 Saturday. Compares what we sent against what the
  vendor acknowledges receiving and opens one ticket per discrepancy. Tickets
  land in billing's queue, not ours, and billing triages them Monday morning. No
  false positives in eleven weeks — but it has never run through a month-end
  close, when the ledger backdates entries into a period we have already
  reported on, so treat a first month-end discrepancy as unproven rather than
  real.
- **Environments.** Production and your laptop. There is no staging, and that is
  not an oversight anyone is getting around to fixing: the vendor bills per
  tenant and finance declined a second one in March. Ask them before assuming
  one can be spun up.
- **Access.** Production is through the bastion. Request it in #platform-access;
  granted eight hours at a time, no auto-renew.
- **Repo conventions.** Branch naming, commit format, and review requirements
  live in `CONTRIBUTING.md`, and that file governs. Section 4, on force-pushing,
  is the one that catches people out — read it before rebasing anything
  that has already been pushed.

## Appendix: local setup

Python 3.11 or newer:

- macOS — `brew install python@3.11`
- Debian/Ubuntu — `apt install python3.11 python3.11-venv`

Then, in the repository root:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
```

Tests are `pytest -q` and take about ninety seconds. If `pytest` cannot find the
package, you have almost certainly not activated the virtualenv — the single
most common setup problem, and worth checking before anything else.

`docker-compose.yml` in the repository root brings up a local Postgres on port
5433. It is only used by the tests; nothing in normal operation touches it.
