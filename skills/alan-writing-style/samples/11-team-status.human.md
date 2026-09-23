The **nightly import** failed Monday and Tuesday nights because Norvell changed their export on 2026-09-21 without telling us. It is **fixed**, deployed on `ops-1`, and both nights are backfilled -- `/stock` serves Tuesday's data (`as_of=2026-09-22T02:07:38Z`, UTC) and `NV-44812` matches the raw CSV row, `as_of` included.

I am off until tomorrow.

Detail is in **`fix/supplier-timestamp-formats`**, open against `main`.

Root cause: Two changes from Norvell landed in Monday's file. The column was renamed `updated` -> `updated_at`, which broke nothing on its own. The value format went from `2026-09-20 03:14:00` to `2026-09-21T02:04:11Z`, which is not supported by the format string.

**Assumptions**

- The old `updated` column was Berlin local, not UTC. **@Priya**
- The `Z` format is permanent, not someone flipping a flag. **@Priya**
- Tonight is handled. **@Tomas** **@Priya** you hear from it only if it breaks, and the mail now actually reaches you.
- Acceptable to have no validation layer at the import boundary, `load.py` left unsplit, and one remaining ruff warning. **@Tomas**
- Acceptable to detect the format once per file rather than per row, and to leave `tz_localize` raising on the ambiguous hour rather than guessing. **@Tomas**

## TODO

- **@Tomas** review the PR.
- **@Priya** ask Norvell whether the `Z` format is permanent or someone flipped a flag, whether the old `updated` column was Berlin local, and whether they can send us a changelog on export changes. Two facts for them: the format change landed 2026-09-21, and it hit the column name and the value format at once, which reads as a deliberate release rather than drift.
- `SFTP_DIR` -> `SUPPLIER_SFTP_DIR`. I renamed it, then found `/opt/deploy/inventory-sync.sh` passing the old name in, and reverted completely, docs table included. It needs both repos moved in one change. **@Tomas** worth picking up if you are in that repo anyway.
- The 36h question: whether `/stock` should refuse stock older than 36 hours instead of publishing a stale `as_of`. **@Tomas**'s call, and I have not touched `api/app.py`.
- Unrelated: `load.py:87` still calls `DataFrame.applymap`, deprecated and an error in a future pandas major.

## Additional notes

- Timestamps we stored before today is wrong by the local offset since the start (two hours in summer, one in winter). It stayed invisible because the `as_of` we publish was wrong by the same amount.
- Postgres: rows stored before today are naive Berlin while new rows are UTC, so the table is internally inconsistent right now. No migration -- tonight's upsert rewrites the whole catalogue, so it has a lifetime of hours.
- Norvell sent a newsletter last week, "API and export improvements". I deleted it unread, so whether it announced this is unknown. Either way, a newsletter is not a changelog.
- Alerting was dead, which is why nobody heard. The `OnFailure=` unit fired both nights and mailed `lukas.reinhard@`, who left in March. Recipient changed to `ops-inventory@norvell-group.example`, reloaded, and tested by triggering the failure unit directly. That edit is on `ops-1` and not in the branch.
- Backfill ran by hand on `ops-1` with `IMPORT_FILE_DATE` set for each run and unset again afterwards -- checked, so tonight takes Wednesday's file. 410,883 and 411,274 rows, about 5m50 each, in line with the historical runtime.
