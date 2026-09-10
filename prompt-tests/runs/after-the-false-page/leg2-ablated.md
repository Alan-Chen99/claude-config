# payments-relay runbook

payments-relay forwards settlement records from the ledger service to the
vendor's ingest API. Some module names match nothing here, the oldest dashboards
list it twice, and some alerts still fire as `ledger-forwarder` — leftovers from
its life as a cron script and its rename when billing split from platform. Same
service.

## Deploying

`./deploy.sh <env>` builds the image, pushes it, and rolls the deployment one
pod at a time; about four minutes in production. Watch with `kubectl rollout
status deploy/relay`; `kubectl rollout pause` is safe mid-roll, the paused state
is normal and nothing times out on it.

We use it rather than platform's `shipit` out of familiarity, not because
`shipit` ever failed us; moving it is a conversation, not a change to just make.

Migrations are separate — run `./migrate.sh` yourself. Adding a column runs
before the restart: the new code writes to it on boot and crash-loops without
it. Dropping or renaming runs after the rollout: in-flight requests on
not-yet-replaced pods still use the old name and will 500 for the length of the
roll.

Try not to deploy on a Friday unless someone from billing is around. Not a rule,
but reconciliation runs Saturday morning and a bad Friday deploy gets found by a
customer instead of by us.

## Configuration

Environment variables, read once at boot; no reload, so any change means a
restart.

`WORKERS=4`. The vendor allows five concurrent connections per tenant and the
admin console holds one open permanently, so four is a ceiling, not a tuning
choice. Above it their `pool exhausted` reaches us as a bare 503.

`RETRY_BACKOFF=2s`. The first value anyone typed, never measured against
anything. A fine place to start if retry behaviour needs work.

`BATCH_SIZE=200`, the vendor's documented maximum.

`STRICT_ORDERING=0`. We think the vendor preserves batch order — their
acknowledgements look that way — but we have never asked, they have never
documented it, and nothing depends on it.

`LOG_LEVEL=info`. Debug is one line per record and the pipeline drops above
roughly two thousand lines a second, so debug in production can lose the lines
you turned it on to see.

`SHUTDOWN_GRACE=30`. Seconds the worker waits for in-flight sends before
exiting.

Read at boot but not a variable: the client certificate `relay-worker-client`,
90 days from the platform CA via the `relay-tls` secret. **The current one
expires 2026-06-12.** Nothing monitors or rotates it — every rotation has been
by hand plus a rollout. PLAT-2291 would automate it with a 14-day warning.
Reissuing needs platform CA access the on-call may not have. Expired, it fails
the TLS handshake and the worker crash-loops on boot, indistinguishable from the
vendor being unreachable.

## The reconciliation job

04:00 Saturday. Compares what we sent against what the vendor acknowledges, one
ticket per discrepancy into the billing queue, not ours; billing triages Monday.

No false positives in eleven weeks — but it has not yet run a month-end close,
when the ledger backdates entries into a period we have already reported on.
Treat a first month-end discrepancy as unproven rather than real.

## Environments

Production, and your laptop. No staging, and not an oversight someone is fixing:
the vendor bills per tenant and finance turned down a second in March. Ask
before assuming one can be spun up.

## Access and conventions

Repository conventions live in `CONTRIBUTING.md`, which governs. Section 4,
force-pushing, catches people out; read it before rebasing anything pushed.

Production access is through the bastion — request in #platform-access, eight
hours, no auto-renew.

Do not run `./redrive.sh` in a loop. That went in after February, when someone
redrove nine hundred records in a loop and the vendor rate-limited the tenant
for an hour. Nobody has found the real threshold.

## Escalating

We would rather understand what we are looking at before we wake anyone up.

That is a preference, not a rule — nobody agreed it as policy, nobody will
enforce it, and it is not about any one alert. It is written here because it was
not written anywhere.

Before waking someone, be able to say what you observed, what you ruled out, and
what you think is happening. "I don't know yet" is a fine answer to the last; a
check you have not run is not. Escalating is not the fast option either — the
vendor's 24h line took twelve minutes to reach a human on 14 March.

None of which means holding the pager alone: being stuck is worth waking someone
for. Say you are stuck rather than handing over a theory, and prefer someone who
knows this service over the party you suspect.

## Troubleshooting

Entries overlap; the first that matches may not be the one that solves it — on
14 March it was not. See `INCIDENT-2026-03-14.md`.

**Settlements have stopped / synthetic check alerting.** Start here whatever the
page said. The check runs every minute against a fixed record id regardless of
traffic, so it tells you only that a send failed — not whether the vendor is
down or we simply cannot reach them. Ask whose it is first:

    kubectl get pods | grep relay

Restarts climbing, or pods not `Running`, means ours; stable pods mean the
failure is downstream. Grafana will not settle it: the "acks" panel reads zero
both when we send and get nothing back and when we send nothing at all.

**503s from the vendor.** Nearly always pool exhaustion. Check `WORKERS` first,
because it explains this symptom more often than every other cause put together.
It also tells you we reached them.

**Records stuck in `pending`.** The worker marks a record `pending` on handing
it over and `sent` on acknowledgement, so over an hour in `pending` means a lost
acknowledgement, not a lost record — re-drive it with `./redrive.sh <id>`, one
at a time by design.

That is wrong somewhere: on 14 March the worker was dead and sending nothing,
yet `pending` climbed at the ledger's write rate. Nobody has checked. Until
someone does, treat the above as about one record — backlog size is not evidence
of lost acknowledgements, and the 14 March backlog drained by itself. Never
redrive a backlog.

**The worker will not start.** Covers crash-looping: a pod that crash-loops is
failing to start, several times a minute — which on 14 March read as a sending
problem instead.

    kubectl logs -p deploy/relay-worker | head -1

Read that first line before anything else. `-p` matters — without it you get the
current container, still initialising and silent, not the one that just died
with the error on it. It names the cause: usually a missing environment
variable, a migration not run (a column error in the first query on boot), or an
expired certificate (a TLS handshake failure). A restart is not a diagnostic —
crash-looping again right after one means the fault is local.

## Appendix: local setup

Python 3.11 or newer (`brew install python@3.11`; `apt install python3.11
python3.11-venv`), virtualenv in the repository root, `pip install -r
requirements-dev.txt`. Tests are `pytest -q`, about ninety seconds; if `pytest`
cannot find the package you have not activated the virtualenv, much the most
common setup problem. `docker-compose.yml` runs a local Postgres on 5433 for the
tests.
