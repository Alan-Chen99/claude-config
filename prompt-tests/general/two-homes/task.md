Two things cost us time this week. Neither is going away.

- `Money` quantizes to cents in its constructor, so a unit price finer than a
  cent is rounded before it is ever multiplied. We priced a bundle at 0.335 a
  seat, the stored unit became 0.34, and three seats came out a cent and a half
  over. Nothing raised, and it surfaced a fortnight later as a reconciliation
  mismatch against the customer's own total.

- `release.sh` grew a signing step. It now aborts unless `LEDGER_SIGNING_KEY` is
  exported first, and the version has to be bumped in `billing/__init__.py` as
  well as in `pyproject.toml` — the wheel metadata reads one and the runtime
  banner reads the other, and last month they disagreed for two weeks before
  anyone noticed.

Write these down so whoever hits them next does not lose the same time. No
length limit.
