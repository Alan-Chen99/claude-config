## Manual import

- Runtime: about 40s to parse (measured once, the 2026-09-21 backfill) and 5-6 minutes to upsert a full catalogue of ~411,000 rows (the 2026-09-21 and 2026-09-22 backfills).
- Failure alert: a failed run mails `ops-inventory@norvell-group.example` through `inventory-import-failure@.service`.

---

Comment:

Adding no docs would have been ok too. Nothing is broken, so nothing need changed.

Suppose that you add

> - Several nights: one day at a time, oldest first, and wait for `Deactivated successfully` before the next. The upsert covers the whole catalogue, so a later day overwrites an earlier one.

than **I** have to verify and be responsible if that is false.

It is also an overclaim, since its taken out of context of one agent session and telling future to just copy it blind. You as writer is not even the runtime agent, you dont server access to verify it.

Thats not neccessary.
