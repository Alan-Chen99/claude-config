# payments-relay runbook

We forward settlement records from the ledger to the vendor's ingest API. Older
alerts fire as `ledger-forwarder`, some source module names match nothing here,
and the oldest dashboards list us twice. All one service.

## Deploying

`./deploy.sh <env>` rolls it out. `kubectl rollout pause` is safe; nothing times
out on a paused roll.

We use that script rather than the platform team's `shipit`. Both worked, and we
kept the script because the team knew it. Moving is a conversation, not a change
to just make.

Run `./migrate.sh` yourself. A column add goes before the restart; a drop or
rename goes after the roll finishes.

Nobody enforces this and it is not a rule, but try not to deploy on a Friday
without billing around. Reconciliation runs Saturday, so a bad Friday deploy is
found by a customer rather than by us.

## Configuration

Environment variables, read once at boot, so a change means a restart.

- `WORKERS=4` — worked before; nobody tuned it.
- `RETRY_BACKOFF=2s` — never measured. A fine place to start if retries need work.
- `BATCH_SIZE=200` — a vendor limit, not ours.
- `STRICT_ORDERING=0` — we think they ingest in send order, going on their
  acknowledgements alone. We never asked, and they never documented it.
- `LOG_LEVEL=info` — debug drops above ~2,000 lines a second, losing the lines
  you turned it on to see.
- `SHUTDOWN_GRACE=30` — seconds the worker waits for in-flight sends.

The vendor's pool is 5 connections per tenant. The admin console holds 1.

## Everything else

**Reconciliation** runs Saturday 04:00 and tickets billing. No false positive in
eleven weeks, but it has never seen a month-end close, when the ledger backdates
into a period we already reported. Treat a first month-end discrepancy as
unproven.

**There is no staging**, and that is not an oversight: the vendor bills per
tenant and finance turned down a second in March. Ask before assuming one can be
spun up.

**`CONTRIBUTING.md` governs** repository conventions. Section 4, on
force-pushing, catches people out.

**Never run `./redrive.sh` in a loop.** One February incident redrove about 900
records and rate-limited the tenant for an hour. Nobody knows the threshold.

## Troubleshooting

**503s from the vendor.** Nearly always pool exhaustion. Check `WORKERS` first.

**Records stuck in `pending`.** A record is `pending` on hand-off and `sent` on
their acknowledgement. Over an hour means a lost acknowledgement, not a lost
record. Redriving is safe: `./redrive.sh <id>`, one id at a time by design.

**Alerts with no traffic.** A synthetic check runs every minute against a fixed
record id, independently of what we send.
