# payments-relay runbook

payments-relay forwards settlement records from the ledger service to the
vendor's ingest API. It started life in 2023 as a cron script, moved to a
long-running worker in early 2024, and picked up its current name when the
billing team split off from platform. A few of the older alerts still fire under
the name `ledger-forwarder`; that is this same service. None of that history
changes how you operate it today, but it does explain why several module names
in the source do not match anything in this document, and why the oldest
dashboards have two entries for what is one thing.

## Deploying

Deploys go out through `./deploy.sh <env>`. The script builds the image, pushes
it, and rolls the deployment one pod at a time. A roll takes about four minutes
in production. You can watch it with `kubectl rollout status deploy/relay`, and
if you need to stop it mid-roll, `kubectl rollout pause` works and is safe — the
paused state is a normal state and nothing times out on it.

We deploy through that script rather than through the platform team's `shipit`
pipeline. Both were run in parallel through most of 2024 and both worked; we
stayed on the script because the team already knew it, not because `shipit` ever
failed us. If you want to move it, that is a conversation to have, not a change
to just make.

Migrations are not part of the deploy. You run `./migrate.sh` yourself, and the
order depends on what the migration does. A migration that adds a column runs
before the restart, because the new code writes to that column on boot and will
crash-loop without it. A migration that drops or renames a column runs after the
rollout finishes, because in-flight requests on the not-yet-replaced pods still
reference the old name and will 500 for as long as the roll takes.

Try not to deploy on a Friday unless someone from billing is around. Nobody
enforces this and it is not a rule, but the reconciliation job runs Saturday
morning, and a bad Friday deploy tends to get discovered by a customer instead
of by us.

## Configuration

Everything is environment variables, read once at boot. There is no reload
mechanism, so changing any of these means a restart.

`WORKERS=4`. The vendor's connection pool allows five concurrent connections per
tenant and the admin console holds one of them open permanently, so four is the
ceiling rather than a tuning choice. Going above it produces `pool exhausted` on
the vendor side, which reaches us as an undifferentiated 503.

`RETRY_BACKOFF=2s`. This was the first value anyone typed and it has never been
measured against anything. If retry behaviour ever needs work, this is a fine
place to start.

`BATCH_SIZE=200`, which is the vendor's documented maximum.

`STRICT_ORDERING=0`. We think the vendor ingests a batch in the order we send
it — that is what their acknowledgements have always looked like — but we have
never put the question to them and they have never documented it. Nothing we run
today depends on the answer.

`LOG_LEVEL=info`. Debug is extremely loud — one line per record — and the log
pipeline starts dropping above roughly two thousand lines a second, so turning
on debug in production can lose the exact lines you turned it on to see.

`SHUTDOWN_GRACE=30`. Seconds the worker waits for in-flight sends before exiting.

## The reconciliation job

It runs at 04:00 on Saturday, compares what we sent against what the vendor
acknowledges receiving, and opens one ticket per discrepancy. The tickets land
in the billing queue, not ours, and someone from billing triages them on Monday
morning.

It has not produced a false positive since it was deployed eleven weeks ago. It
has also not yet run through a month-end close, which is when the ledger service
backdates entries into a period we have already reported on, so treat a
discrepancy raised at the first month-end as unproven rather than as real.

## Environments

There is production, and there is your laptop. There is no staging.

This is not an oversight that someone is getting around to fixing. The vendor
bills per tenant, and finance turned down a request for a second tenant in
March; ask them before assuming one can be spun up.

## Access and conventions

Repository conventions — branch naming, commit format, review requirements —
all live in `CONTRIBUTING.md`, and that file is what governs. The section that
catches people out is section 4, on force-pushing, so read it before you rebase
anything that has already been pushed.

Production access is through the bastion. Request it in #platform-access; it is
granted for eight hours at a time and does not auto-renew.

Do not run `./redrive.sh` in a loop. That went in after one incident in
February, when someone redrove about nine hundred records in a shell loop and
the vendor rate-limited the whole tenant for an hour; it has not come up since,
and nobody has worked out where the actual threshold is.

## Troubleshooting

**503s from the vendor.** Nearly always pool exhaustion. Check `WORKERS` first
before you go looking at anything else, because it explains this symptom more
often than every other cause put together.

**Records stuck in `pending`.** The worker marks a record `pending` when it
hands it to the vendor and `sent` when the vendor acknowledges. A record that
sits in `pending` for more than an hour means an acknowledgement was lost, not
that the record was lost. Re-driving it is safe. There is a script for this,
`./redrive.sh <record-id>`, and it takes one id at a time by design.

**The worker will not start.** Nine times out of ten this is a missing
environment variable, and the error message names it. Read the first line of the
crash output before doing anything else. The second most common cause is a
migration that has not been run, which looks like a column error in the first
query the worker makes on boot.

**Alerts firing with no traffic.** The synthetic check runs every minute against
a fixed record id and will alert on its own if the vendor is down, even when we
are sending nothing. Check the vendor status page before you page anyone.

## Appendix: local setup

You need Python 3.11 or newer. On macOS, `brew install python@3.11`; on Debian
and Ubuntu, `apt install python3.11 python3.11-venv`. Then make a virtualenv in
the repository root with `python3.11 -m venv .venv`, activate it with
`source .venv/bin/activate`, and install the dependencies with
`pip install -r requirements-dev.txt`. The test suite is `pytest -q` and takes
about ninety seconds. If `pytest` cannot find the package, you have almost
certainly forgotten to activate the virtualenv, which is the single most common
setup problem and worth checking before anything else.

There is a `docker-compose.yml` in the repository root that brings up a local
Postgres on port 5433. It is only used by the tests; nothing in normal operation
touches it.
