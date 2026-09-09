# payments-relay runbook

Forwards settlement records from the ledger service to the vendor's ingest API.
Some old alerts still fire as `ledger-forwarder`, several source modules match
neither name, and the oldest dashboards list it twice; it is all one service.

## Deploying

`./deploy.sh <env>` rolls one pod at a time. `kubectl rollout pause` is safe; paused is a normal state and nothing times out on it.

We use that script over the platform team's `shipit` pipeline. Both ran in parallel
through 2024 and both worked; we stayed on the script because the team knew it,
not because `shipit` failed. Moving is a conversation, not a change to just make.

**Migrations are separate.** Run `./migrate.sh` yourself; order depends on the
migration.

- **Adds a column — before the restart.** New code writes to it on boot and
  crash-loops without it.
- **Drops or renames a column — after the roll finishes.** Not-yet-replaced pods
  still reference the old name and 500 until they are gone.

Try not to deploy on a Friday unless billing is around. Nobody enforces this and
it is not a rule, but reconciliation runs Saturday, and a bad Friday deploy tends
to get found by a customer instead of by us.

## Configuration

Environment variables, read at boot; no reload, so a change means a restart.

- `WORKERS=4` — a ceiling, not a tuning choice: the vendor allows five
  concurrent connections per tenant, and the admin console permanently holds
  one. Above four you get `pool exhausted`, which reaches us as an
  undifferentiated 503.
- `BATCH_SIZE=200` — the vendor's documented maximum.
- `RETRY_BACKOFF=2s` — the first value anyone typed, never measured; a fine
  place to start if retry behaviour needs work.
- `STRICT_ORDERING=0` — we think the vendor ingests a batch in the order we send
  it, from their acknowledgements alone. We have never asked them and they have
  never documented it. Nothing we run today depends on the answer.
- `LOG_LEVEL=info` — debug is one line per record; the pipeline drops above ~2000
  lines/sec, so it can lose the lines you turned it on to see.
- `SHUTDOWN_GRACE=30` — seconds to wait for in-flight sends before exiting.

## Troubleshooting

**503s from the vendor.** Nearly always pool exhaustion — check `WORKERS` before
anything else.

**Records stuck in `pending`.** `pending` means handed to the vendor, `sent`
means acknowledged. Over an hour in `pending` is a lost acknowledgement, not a
lost record, so re-driving is safe: `./redrive.sh <record-id>`, one id at a time
by design. **Never loop it**: one February incident, about nine hundred redrives
in a shell loop, rate-limited the whole tenant for an hour. It has not come up
since, and nobody has worked out the real threshold.

**The worker will not start.** Often a missing environment variable, named in
the first line of the crash output; also an unrun migration showing as a column
error on boot.

**Alerts firing with no traffic.** The synthetic check hits a fixed record id
every minute and alerts on its own if the vendor is down, even when we send
nothing. Check the vendor status page before paging anyone.

## Reconciliation

Runs 04:00 Saturday and opens one ticket per discrepancy into the **billing**
queue, not ours; billing triages Monday.

No false positives in the eleven weeks since deploy — but it has not yet run
through a month-end close, when the ledger backdates entries into a period we
have already reported. Treat a first month-end discrepancy as unproven.

## Access and environments

Production and your laptop; **no staging**. Not an oversight awaiting a fix: the
vendor bills per tenant and finance turned down a second tenant in March — ask
them before assuming one can be spun up.

`CONTRIBUTING.md` governs repository conventions. Section 4,
on force-pushing, is the one that catches people out — read it before rebasing
anything already pushed.
