# Ratings 01: messages

Four contexts you know (09, 12, 14, 15), two candidates each, from two versions of the skill. The order is shuffled; which version wrote which goes in at the end after you rate. 06 is left out: both versions give your line word for word.

Under each candidate fill in the two lines. `Verdict:` acceptable or not, as a message you would send as it stands, not whether it is the one you would have written. `Why:` a few words on what decides it; for a not, the one thing that would have to change.

## 09: Message to a colleague, sent in chat

They posted the weekly benchmark numbers: a 12% regression on one benchmark, which they put down to your change from Monday. You looked at the run: the nightly job was running on the shared machine (the run log shows it starting 4 minutes into the run), and the other benchmarks in the same run are within 1% of last week. You want that one benchmark rerun on an idle machine before anyone reverts anything.

### 09-A

The run log has the nightly job starting 4 minutes into that benchmark, so it was sharing the machine. Rerun that one on an idle machine before reverting?

Verdict: 8/10
Why:

### 09-B

The run log shows the nightly job starting 4 minutes into that run. Rerun on an idle machine?

Verdict: 9/10
Why: I am possibly more likely to say "There is a nightly job starting 4 minutes into that run", but if i review myself i may find your form actually better practically.

## 12: Message to Priya, sent in chat

The one you said at 17:12 in the log you would send: she is to ask Norvell about the export change. Material: the day's log, all of it available, none of it required.

### 12-A

Norvell's stock export switched to UTC timestamps with a `Z` on 2026-09-21. Ask them whether that is permanent, and whether they can send us a changelog for export changes?

Verdict: 9/10
Why: maybe "can send us" -> "can send"

### 12-B

Norvell's stock export changed the timestamp format on 2026-09-21, from `2026-09-20 03:14:00` to `2026-09-21T02:04:11Z`. Ask them whether that is permanent or someone flipped a flag, and whether they can send us a changelog for export changes?

Verdict: 8/10
Why:

## 14: Reply to Mira, sent in chat, under 150 words

Thursday morning she wrote: "Read your status, thanks. The weekly stock-age report runs off the same table and flags every SKU whose timestamp is older than 48 hours. Your note says SKUs that dropped out of the export keep the old naive value -- how many are those, and do they get fixed at some point? I would rather not filter them by hand every Monday." Nobody has counted those SKUs. A one-off migration was proposed at 10:36 and skipped at 10:38; that dropped SKUs keep the old value was noticed only when the status was written. A migration or a delete would be yours to write; Tomas reviews.

### 14-A

Nothing changed for your report except the zone: every SKU still in the export moved two hours earlier today.

> how many are those

Nobody has counted them.

> do they get fixed at some point

Not on their own -- the upsert does not delete, so a SKU that drops out of the export keeps the value it had on its last appearance.

> I would rather not filter them by hand every Monday.

I can shift those rows by the offset, or delete what is no longer in the export. Which do you prefer? Either is mine to write, Tomas reviews.

Verdict: 3/10
Why: "Nobody has counted them." doesnt answer the question. It does not even answer "could someone have counted it". "the upsert does not delete" I would not use becuase real reason this does not work is _the feature not yet implmented_, and I need to make that very clear, and that means not putting "upsert does not delete" as the primary reason. I can maybe consider explaning if that is made clear.

### 14-B

Only the zone changed on your side: every SKU still in the export was rewritten to UTC yesterday, which moves its timestamp by two hours.

> SKUs that dropped out of the export keep the old naive value

Still true.

> how many are those

Nobody has counted them.

> do they get fixed at some point?

Not on their own -- the upsert never deletes.

> I would rather not filter them by hand every Monday.

I can shift the old rows by the offset, or delete what is no longer in the export. Which do you prefer?

Verdict: 3/10
Why: same as 14a

### 14-C

Written after your 14-A and 14-B verdicts went into the skill (a state on his side is explained by what is not done yet, not by the mechanism; a question about it is answered with what he has or can do).

Nothing changed on your side except the zone: rows still in the export moved by two hours.

> how many are those

Not counted. I can get you the number.

> do they get fixed at some point?

Not on their own, and I have not written anything for it yet.

> I would rather not filter them by hand every Monday.

I can shift the old rows by the offset, or delete the ones that dropped out of the export. Either is mine to write and Tomas reviews. Which is preferred?

Verdict:
Why:

## 15: Email to Dana Okafor, integrations at Norvell, under 150 words with a subject line

The address is from Norvell's export documentation. Dana has never heard from you, does not know what your import does with the file, and may not know anything changed for anyone. Priya is out this week, so you write directly, on 2026-09-24. You want: whether the new format is permanent or a flag someone flipped; whether the old `updated` values were Berlin local time; a changelog, or notice before export changes. You know: in `stock_2026-09-21.csv.gz` the column `updated` became `updated_at` and the values went from `2026-09-20 03:14:00` to `2026-09-21T02:04:11Z`; that broke your import for two nights; it is fixed on your side and accepts both. The file name is Norvell's own: their SFTP publishes `out/stock_<date>.csv.gz` (log line 7, `fetching sftp://feeds.norvell-supply.net/out/stock_2026-09-22.csv.gz`); the unpacked copy on `ops-1` is `/srv/supplier/stock_<date>.csv`.

### 15-A

Subject: Stock export format change on 2026-09-21

Hi Dana,

We import your nightly stock export from `feeds.norvell-supply.net`; your export documentation gives this address for integration questions.

In `stock_2026-09-21.csv.gz` the column `updated` became `updated_at` and its values went from `2026-09-20 03:14:00` to `2026-09-21T02:04:11Z`. Both changes landed in that one file. That broke our import for two nights; it is fixed on our side and takes either format.

Three questions:

- Format: is `2026-09-21T02:04:11Z` permanent, or a flag someone flipped?
- Zone: were the old `updated` values Berlin local time?
- Changelog: is there one for the export, or can we get notice before it changes?

Thanks,
Alan

Verdict:
Why:

### 15-B

Subject: Stock export format change, 2026-09-21

Hi Dana,

We import your nightly stock export. In `stock_2026-09-21.csv.gz` the column `updated` became `updated_at` and its values went from `2026-09-20 03:14:00` to `2026-09-21T02:04:11Z`.

Is the new format permanent or did someone flip a flag, was the old `updated` column Berlin local time, and do you publish a changelog for export changes?

Thanks,
Alan

Verdict:
Why:

## 11: End-of-day status in the team channel

Your addition: a doc, where you expect the skill to possibly not do well. Readers: Priya and Tomas, who were not there today and will read this instead of asking; you are off until tomorrow. Material: the day's log, all of it available, none of it required. Your own version is `11-team-status.human.md`. Content errors count against a candidate the same as writing does; name them in Why.

### 11-A

# Supplier import

`/stock` is serving Tuesday again -- `as_of=2026-09-22T02:07:38Z`, UTC. Norvell changed their export on 2026-09-21 and that killed Monday's and Tuesday's imports; the fix is deployed on `ops-1` (`d0f9e22`) and both nights are backfilled. Tonight's 02:30 is the first unattended run through the new code. I am off until tomorrow.

The failure alert did fire, both nights, to `lukas.reinhard@`, who left in March, which is why nobody heard it: alerting on this service has been dead since spring. Recipient is now `ops-inventory@norvell-group.example`, reloaded and tested by triggering the failure unit directly.

Detail is in `fix/supplier-timestamp-formats` (PR open against `main`) and in `docs/operations.md` under "Supplier export".

## Root cause

Two changes in the same file on 2026-09-21: the timestamp column renamed from `updated` to `updated_at`, and the value format moved from `2026-09-20 03:14:00` to `2026-09-21T02:04:11Z`. The rename did not break us on its own; the format did. Both moving at once reads as a deliberate release rather than drift. They sent a newsletter last week titled "api and export improvements" -- whether it announced this is unknown, since it was deleted unread.

## Timezone offset

The old column carried no zone and we stored it as it came, as if it were UTC. Norvell is in Bremen, so the old values were almost certainly Europe/Berlin local -- inferred from the offset between Sunday's and Monday's rows, not confirmed with them. If that is right, every row and every `as_of` we have published was off by the local offset for as long as this job has run, two hours in summer and one in winter -- invisible, because both were off by the same amount.

The backfill rewrote the catalogue in UTC, so Postgres is right now for everything in Tuesday's file. The run reports only inserts and updates (inserted 402, updated 410872), so a SKU that has dropped out of the supplier's file still holds its old naive value.

## Assumptions

Decided today without you. Tomas can overrule any of them on the PR.

- Supplier zone: `ZoneInfo("Europe/Berlin")` rather than a fixed `+02:00`, so October's transition needs no second edit. `tz_localize` then raises on the ambiguous hour and the export runs around 03:00 local, inside it. Left raising rather than guessing.
- Format detection: from the first non-null value rather than per row, so a file mixing both formats would be misparsed.
- No migration for the naive rows: the backfill has already rewritten them.
- `SFTP_DIR` -> `SUPPLIER_SFTP_DIR`: renamed, then reverted. `/opt/deploy/inventory-sync.sh` passes `SFTP_DIR` in and is not in our repo, so renaming on our side alone would fail at fetch time.
- `ruff` TRY003 on the new error message: left standing, the long message is the point of it.

## TODO

- Tomas: review `fix/supplier-timestamp-formats`. No deadline -- tonight's run goes ahead either way.
- Tomas: the 36h question, whether `/stock` should refuse to serve stock older than 36 hours rather than publish a stale `as_of`. Your call, you wrote it, and I have not touched `api/app.py`.
- Tomas: the `SFTP_DIR` rename, if you want it, both sides in one change.
- Priya: ask Norvell whether the `Z` format is permanent or someone flipped a flag, and whether they can send us a changelog for export changes. The two facts worth putting in front of them are the date, 2026-09-21, and that the column name and the value format moved at the same time.

## Additional notes

- Backfill: 410883 rows for Monday and 411274 for Tuesday, about 5m50 each, in line with the historical runtime. `IMPORT_FILE_DATE` is unset again (checked), so tonight takes Wednesday's file. Spot-checked `NV-44812` against the raw CSV and it matches, `as_of` included.
- `load.py:87` uses `DataFrame.applymap`, deprecated and an error in some future pandas major. Not today's failure, but worth fixing sometime.

Verdict:
Why:

### 11-B

The nightly supplier import failed Monday and Tuesday night and is fixed. Both nights are backfilled, so `/stock` has served Tuesday's file since 13:20 instead of Sunday's (`as_of=2026-09-22T02:07:38Z`, UTC). I am off until tomorrow. Detail is in `fix/supplier-timestamp-formats`, PR open against `main`, and in `docs/operations.md` under Supplier export.

## Root cause

Norvell changed the export on 2026-09-21: the timestamp column moved from `updated` to `updated_at`, and the values from `2026-09-20 03:14:00` to `2026-09-21T02:04:11Z`. The rename alone did not break us; the format did. They announced it in a newsletter last week ("api and export improvements") and I deleted it unread.

## Stored timestamps

The old column carried no zone and we stored it as UTC. Norvell sits in Bremen and the same export reads two hours earlier in the new format, so the old values were most likely Europe/Berlin local (inferred, not confirmed by them): every timestamp stored before Monday is off by two hours in summer, one in winter. The `as_of` we publish was off by the same amount, which is why nothing looked wrong.

The backfill rewrote every SKU in Tuesday's file with UTC values. A SKU that has dropped out of the file since was not touched and keeps its naive value; I have not counted those, and a delete or a shift is mine to write.

## Done today

- Loader: takes `updated_at` or `updated`, parses either format, stores UTC, and raises with the full header line when neither name is there. Three tests added, all seven pass.
- Backfill: Monday and Tuesday run by hand on `ops-1`, 410,883 and 411,274 rows, about 5m50 each (checked `NV-44812` against Tuesday's CSV: quantities, cost and `as_of` match). The `IMPORT_FILE_DATE` override is cleared, so tonight takes Wednesday's file.
- Alerting: `OnFailure=` mailed `lukas.reinhard@`, who left in March, so both nights' alerts reached nobody. Recipient is now `ops-inventory@norvell-group.example`, tested by triggering the failure unit.
- Docs: both column names and both formats are in `docs/operations.md`.

## Assumptions

- Berlin local: the old values are Europe/Berlin, inferred from the offset and from where Norvell sits, not confirmed. @Priya's question to them settles it.
- First value: the format is taken from the first non-null value in the file, not per row, so a file mixing both would be misparsed. @Tomas.
- Ambiguous hour: localised with `ZoneInfo("Europe/Berlin")` rather than a fixed `+02:00`, so October needs no second edit; `tz_localize` raises on the ambiguous hour and Norvell exports inside that window. Left raising rather than guessing. @Tomas.

## TODO

- @Tomas: review the PR tomorrow.
- @Tomas: whether `/stock` should refuse to serve stock older than 36h instead of publishing a stale `as_of`. Your call, you wrote the API, and I have not touched `api/app.py`.
- @Priya: ask Norvell whether the `Z` format is permanent or someone flipped a flag, and whether they can send a changelog for export changes. Worth giving them: the change date, 2026-09-21, and that the column name and the value format moved together, which reads as a deliberate release rather than drift.
- Me: count the rows no longer in the file, then delete or shift them.

## Tonight

02:30 is the first unattended run through the new code. The timer is unchanged, the override is cleared, and a failure now mails the team list.

## Additional notes

- `SFTP_DIR` -> `SUPPLIER_SFTP_DIR`: renamed, then reverted. `/opt/deploy/inventory-sync.sh` passes `SFTP_DIR` in and is not in our repo (@Tomas's). Ours can move when that one does.
- `load.py:87` uses `DataFrame.applymap`, deprecated and an error in some future pandas. Not today's failure (checked); still there.
- `ruff` TRY003 on the new error message, left standing: the message is the point of it.

Verdict:
Why:
