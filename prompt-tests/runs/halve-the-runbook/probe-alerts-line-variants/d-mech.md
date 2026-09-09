# payments-relay runbook

Ledger → vendor ingest API. Older alerts fire as `ledger-forwarder` — same
service.

**Deploy** `./deploy.sh <env>`. `rollout pause` is safe: nothing times out on a
paused roll. Not `shipit` — both worked; we kept the script because the team knew
it. A conversation, not a change to just make. `./migrate.sh` separately: column
adds go **before** the restart, drops and renames **after** the roll finishes.
Nobody enforces this and it is not a rule, but try not to deploy Friday without
billing — reconciliation is Saturday, so a bad one is found by a customer, not us.

**Config**, read at boot. `BATCH_SIZE=200`, `SHUTDOWN_GRACE=30`.

- `WORKERS=4` — a ceiling, not a knob: vendor pool is 5 per tenant, the admin
  console holds 1.
- `RETRY_BACKOFF=2s` — never measured. Free to change.
- `STRICT_ORDERING=0` — we think they ingest in send order, from acks alone;
  never asked, and never documented by them.
- `LOG_LEVEL=info` — debug drops above ~2k lines/s, losing the lines you turned
  it on for.

**Reconciliation** Sat 04:00, tickets to billing. No false positive in eleven
weeks, but never a month-end close, when the ledger backdates into a reported
period — treat a first month-end discrepancy as unproven.

**No staging**, not an oversight: the vendor bills per tenant and finance turned
down a second in March. Ask before assuming.

**`CONTRIBUTING.md` governs**; §4, force-pushing, catches people out.

**Never loop `./redrive.sh`** — one February incident, ~900 records, tenant
rate-limited an hour. Threshold unknown.

**503s** nearly always pool exhaustion; check `WORKERS` first.

**Stuck `pending`** — `pending` on hand-off, `sent` on their ack; over an hour is
a lost acknowledgement, not a lost record. `./redrive.sh <id>`, one at a time by
design.

**Alerts, no traffic** — a synthetic check runs every minute against a fixed
record id, independently of what we send.
