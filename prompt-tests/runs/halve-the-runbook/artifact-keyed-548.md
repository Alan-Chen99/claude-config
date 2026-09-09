# payments-relay runbook

Forwards settlement records from the ledger to the vendor's ingest API. Older
alerts still fire as `ledger-forwarder`; several source module names match
nothing in this document, and the oldest dashboards list it twice.

**Deploy** `./deploy.sh <env>`. `rollout pause` is safe — paused is a normal
state, nothing times out on it. Not `shipit`: both ran in parallel through most
of 2024 and both worked; we kept the script because the team knew it, not
because `shipit` failed — a conversation to have, not a change to just make.
`./migrate.sh` separately, and the order depends on the migration: adds go
**before** the restart (new code writes the column on boot, else crash-loop),
drops and renames **after** the roll (old pods still reference the old name and
500 for its length). Nobody enforces this and it is not a rule, but try not to
deploy Friday without billing — reconciliation runs Saturday, so a bad one is
found by a customer instead of by us.

**Config**, read once at boot — there is no reload, so a change means a restart.
- `WORKERS=4` — a ceiling, not a tuning choice: the vendor's pool is 5 per
  tenant and the admin console holds 1. Above it, `pool exhausted` reaches us as
  an undifferentiated 503.
- `RETRY_BACKOFF=2s` — the first value anyone typed, never measured; a fine
  place to start.
- `BATCH_SIZE=200` — the vendor's documented maximum.
- `LOG_LEVEL=info` — debug is one line per record and the pipeline drops above
  ~2,000 lines/s, so debug in production can lose the lines you turned it on for.
- `STRICT_ORDERING=0` — we think they ingest in send order, from their
  acknowledgements alone; never put to them, never documented by them, and
  nothing today depends on it.

**Reconciliation** Sat 04:00, tickets to billing's queue. No false positive in
eleven weeks, but it has never run a month-end close, when the ledger backdates
into a reported period — treat a first month-end discrepancy as unproven.

**No staging**, and not an oversight: the vendor bills per tenant and finance
turned down a second in March. Ask them before assuming.

**`CONTRIBUTING.md` governs** conventions. §4, force-pushing, is the one that
catches people out — read it before rebasing anything already pushed.

**Never loop `./redrive.sh`** — it went in after one February incident, ~900
records looped, tenant rate-limited an hour. Not come up since, and nobody has
worked out the threshold.

Production access is through the bastion; request it in #platform-access, eight
hours at a time, no auto-renew.

**503s** nearly always pool exhaustion; check `WORKERS` first.

**Worker will not start** — nine times out of ten a missing env var, and the
error message names it, so read the first line of the crash output first. Next
most common is an unrun migration, which looks like a column error in the
worker's first query on boot.

**Stuck `pending`** — set on hand-off, `sent` on the vendor's ack; over an hour
means a lost acknowledgement, not a lost record. Redriving is safe:
`./redrive.sh <id>`, one at a time by design.

**Alerts, no traffic** — the synthetic check runs every minute against a fixed
record id and alerts on its own if the vendor is down, even when we send
nothing. Check the vendor status page before paging anyone.
