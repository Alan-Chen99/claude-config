# payments-relay runbook

Ledger → vendor ingest API. Alerts, dashboards and source module names disagree
on its name; expect mismatches.

**Deploy** `./deploy.sh <env>`. `rollout pause` is safe — paused is a normal
state, nothing times out on it. Not `shipit`: both ran in 2024 and both worked,
we kept the script because the team knew it, not because `shipit` failed — a
conversation to have, not a change to just make. `./migrate.sh` separately: adds
**before** the restart (new code writes the column on boot, else crash-loop),
drops and renames **after** the roll (old pods still use the old name, and 500
for its length). Nobody enforces this and it is not a rule, but try not to
deploy Friday without billing — reconciliation is Saturday, so a bad one is
found by a customer, not by us.

**Config**, read at boot.
- `WORKERS=4` — a ceiling, not a tuning choice: vendor pool is 5 per tenant, the
  admin console holds 1. Above it, `pool exhausted` reaches us as a bare 503.
- `RETRY_BACKOFF=2s` — first value anyone typed, never measured; a fine place to
  start.
- `BATCH_SIZE=200` — the vendor's documented maximum.
- `STRICT_ORDERING=0` — we think they ingest in order, from their acks alone;
  never asked, and nothing today depends on it.

**Reconciliation** Sat 04:00, tickets to billing. No false positive in 11 weeks,
but never yet a month-end close, when the ledger backdates into a reported
period — treat a first month-end discrepancy as unproven.

**No staging**, not an oversight: the vendor bills per tenant and finance
declined a second in March. Ask them before assuming.

**`CONTRIBUTING.md` governs** conventions; §4 is force-pushing.

**Never loop `./redrive.sh`** — one February incident, ~900 records looped,
tenant rate-limited an hour. Not come up since; nobody has worked out the
threshold.

**503s** nearly always pool exhaustion; check `WORKERS` first.

**Stuck `pending`** — set on hand-off, `sent` on the vendor's ack; over an hour
is a lost acknowledgement, not a lost record. `./redrive.sh <id>`, one at a time
by design.

**Alerts, no traffic** — the synthetic check runs every minute against a fixed
record id and alerts on its own if the vendor is down, even when we send
nothing.
