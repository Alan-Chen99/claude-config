# End of day: supplier import

**Short version:** the nightly import has been dead since Monday morning because Norvell changed their export format on 2026-09-21 without telling us. It's fixed, tested, deployed, and both missed nights are backfilled — `/stock` is serving Tuesday's data now. There's a PR waiting for Tomas and a supplier question for Priya. I'm off until tomorrow, so this is written up in more detail than usual.

## Root cause

Two changes landed in Monday's file at once.

- The timestamp column was renamed `updated` → `updated_at`. This one didn't break anything on its own: the loader located the column by prefix match, and `"updated_at".startswith("updated")` is true. It did make the traceback confusing, because it reported a column name none of us had seen before.
- The value format changed from `2026-09-20 03:14:00` to `2026-09-21T02:04:11Z`. This is what broke us. Our format string `%Y-%m-%d %H:%M:%S` consumes the date, then finds `T02:04:11Z` where it expects a space — which is exactly the `unconverted data remains` message in the journal.

Both changes arriving together reads as a deliberate release on their side rather than drift. Norvell sent a newsletter last week titled "API and export improvements". I deleted it.

**Not the cause:** the Dependabot pandas bump (2.2.3 → 2.3.0) that merged Thursday. I spent the morning on it. Both versions fail on Monday's file and both succeed on Sunday's, so the variable is the file, not the library. The bump is exonerated.

## The part that matters more than the outage

The old column carried no zone, and we stored it naive, as if it were UTC. The supplier is in Bremen, so it was almost certainly Europe/Berlin local. Sunday's row for the same export window says `03:14:00`; Monday's says `02:04:11Z`. Same wall-clock moment, two hours apart on paper.

So every timestamp we have stored has been wrong by the local offset — two hours in summer, one in winter — for as long as this job has been running. It was invisible because the `as_of` we publish was wrong by the same amount, so the data was consistent with itself and inconsistent only with reality.

Rows already in Postgres are still naive Berlin while new rows are UTC, so the table is internally inconsistent right now. I chose not to write a migration: tonight's upsert rewrites the whole catalogue anyway, so the inconsistency has a lifetime of hours.

## The fix

Branch `fix/supplier-timestamp-formats`, PR open against `main`. **Tomas, can you review it tomorrow?**

The loader now:

- takes `updated_at` if present, otherwise `updated`;
- parses ISO 8601 values as UTC, and naive values as Europe/Berlin converted to UTC — either way the column written to Postgres is UTC;
- raises immediately with the full header line when neither column is present, so the next time they rename something the journal tells us the new name without anyone opening the CSV.

Three tests added (one row per format, plus a header with neither column to pin the error message). All seven in `tests/test_load.py` pass. Both formats are now documented in `docs/operations.md` under "Supplier export".

Two choices you may want to overrule:

- The format is detected from the first non-null value in the file, not per row, so a file mixing both formats would be misparsed. Per-row branching over 410k rows looked like the worse trade, but it's a one-line change if you disagree.
- I localise with `ZoneInfo("Europe/Berlin")` rather than a fixed `+02:00`, so October's transition needs no second edit. The cost is that `tz_localize` raises on the ambiguous hour, and the supplier exports around 03:00 local, inside that window. I left it raising rather than guessing. It only bites on old-format files, which we may never see again.

## Backfill

Monday and Tuesday are both loaded, run by hand on `ops-1` with `IMPORT_FILE_DATE` set in the manager environment and unset again afterwards (checked — it's clear, so tonight's run won't re-import Monday). 410,883 and 411,274 rows, about 5m50 each, in line with the historical runtime.

`/stock` now returns `as_of: 2026-09-22T02:07:38Z` — that's Tuesday, and it's UTC, so 04:07 local. I spot-checked `NV-44812` against the raw CSV: quantities, cost and currency match the row, and the `as_of` matches the row's own timestamp with no offset applied.

## Alerting was dead, which is why nobody heard

Priya — the `OnFailure=` unit did fire, both nights. It mails `lukas.reinhard@`, who left in March. Alerting on this service has been silently non-functional since spring.

Recipient changed to `ops-inventory@norvell-group.example`, daemon reloaded, and tested by triggering the failure unit directly so no real import had to fail to prove it. The mail arrived.

## Reverted, and not done

- **`SFTP_DIR` → `SUPPLIER_SFTP_DIR`.** I renamed it in our four places, then checked outside the repo and found `/opt/deploy/inventory-sync.sh` passing `SFTP_DIR` in. That's the deploy repo, Tomas's. Renaming on our side alone would have made the loader fall back to `/srv/supplier` as a *remote* path and fail at fetch time instead of at startup. Reverted completely, docs table included. Happy to redo it if the deploy side moves in the same change.
- A pydantic validation layer at the import boundary, and splitting the 241-line `load.py`. Both were proposed, both declined: they improve the failure message, not the time to repair, and the repair is always "read the new file and teach the loader about it".
- `ruff` flags TRY003 on the new error message. Left standing — the long message is the whole point of it.

## Latent, not urgent

`load.py:87` uses `DataFrame.applymap`, which is deprecated and becomes an error in a future pandas major. It came up this morning and I ruled it out — the values reach the parse intact — but it is worth fixing sometime.

## Over to you

- **Tomas:** the PR. Also the 36h question, whether `/stock` should refuse to serve stock older than 36 hours instead of publishing a stale `as_of`. You wrote the API, so it's your call and I haven't touched `api/app.py`. And the `SFTP_DIR` rename, if you want it.
- **Priya:** can you ask Norvell whether the `Z` format is permanent or whether someone flipped a flag, and whether they can send us a changelog for export changes? We shouldn't be finding this out from the job dying. Two facts worth putting in front of them: the change date was 2026-09-21, and it hit the column name and the value format simultaneously, which points at a deliberate release.
- **Tonight:** 02:30 is the first unattended run through the new code. The timer is unchanged (`OnCalendar=*-*-* 02:30:00`), the override is cleared so it takes Wednesday's file by default, and if it fails the alert now reaches the team list rather than Lukas.
