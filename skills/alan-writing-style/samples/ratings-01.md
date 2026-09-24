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

Verdict: 8/10
Why: "Either is mine to write and Tomas reviews." -> "(Tomas will review this)", or remove

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

Verdict: 8/10
Why: "your export documentation gives this address for integration questions." -> "(from your export documentation)"

### 15-B

Subject: Stock export format change, 2026-09-21

Hi Dana,

We import your nightly stock export. In `stock_2026-09-21.csv.gz` the column `updated` became `updated_at` and its values went from `2026-09-20 03:14:00` to `2026-09-21T02:04:11Z`.

Is the new format permanent or did someone flip a flag, was the old `updated` column Berlin local time, and do you publish a changelog for export changes?

Thanks,
Alan

Verdict: 9/10
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

Verdict: 5/10
Why: `Timezone offset` section "hangs in midair". What is the focus? explanation, or the "as_of" thing? Fails to address "key" questions like "is this still a problem" clearly. I read it, and am not sure whether I need to do anything bc of that and what is the extent of the issue.

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

Verdict: 5/10
Why: Also floating, feels "unfocused". And, taking "Priya" as example, how much of this is she supposed to read? They cannot easily tell, and also becuase this is rather long (I suppose the non-additional-notes section is longer so reader is forced to read more). also, both 11-A and 11-B is like, I read all the words but had no idea about my takeaway. I avoid writing like that.

## Key, round 1

new = the skill after the round 8 rewrite (`8aea07d3`); old = the skill before it (`b58638b2`).

- 09-A new 8, 09-B old 9
- 12-A old 9, 12-B new 8
- 14-A new 3, 14-B old 3; 14-C new after the 14 rule change (`2f69b936`), 8
- 15-A new 8, 15-B old 9
- 11-A old 5, 11-B new 5

## Round 2: after the 14-C, 15 and 11 verdicts went into the skill

What changed in the skill from your whys: a side fact the point does not need (who reviews, where an address came from) is a parenthetical or nothing (14-C, 15-A); the offer says whose it is, so `mine to write` is not stated again (14-C); every part of a doc ends in what it means for the reader, the state or whose it is, and a part that only explains hangs in midair (11); a status is ordered by who must read it: the takeaway first with whether it is still a problem, then the lines that are someone's, and explanation last under Additional notes, never in the body, work done not listed (11); with material, a claim the draft has and the material does not is cut (11: `Norvell is in Bremen` is in the ai draft only, not in the log, and all four 11 candidates before this carried it). One candidate per context below, all from the same skill text, so no key.

Regenerated 2026-09-23 evening: the first three candidates here, and every candidate in round 1, were written with this directory's `CLAUDE.md` in the writer's context (it quotes your lines and your verdicts; `CLAUDE.md`, round 11). These three were written from copies outside the repo, so they are what the skill does on its own.

### 11-C

# Supplier import

Norvell changed their stock export on 2026-09-21 and the nightly import has died on it two nights running. Fixed and deployed. Both missed nights are backfilled, so `/stock` is serving Tuesday now, `as_of=2026-09-22T02:07:38Z`. The loader takes either column name and either value format and stores UTC. I am off until tomorrow. The change is on `fix/supplier-timestamp-formats`, PR open against `main`; both formats are written up in `docs/operations.md` under "Supplier export".

## Root cause

Two changes landed in Monday's file at once: the timestamp column was renamed `updated` -> `updated_at`, and the values moved from `2026-09-20 03:14:00` to `2026-09-21T02:04:11Z`. The rename passed through our prefix match unnoticed, since `"updated_at".startswith("updated")` is true; the format change is what broke us, because `%Y-%m-%d %H:%M:%S` consumes the date and then finds `T02:04:11Z` where it expects a space. Both moving in the same file reads as a deliberate release rather than drift.

## Assumptions

All of these are in the PR and all of them are Tomas's to overrule in review.

- Old values: Europe/Berlin local, stored naive as if they were UTC. Inferred from the offset (`03:14:00` Sunday against `02:04:11Z` Monday), not confirmed by the supplier.
- Format detection: from the first non-null value in the file, not per row, so a file mixing both formats is misparsed. Per-row branching over 410k rows looked like the worse tradeoff.
- Ambiguous hour: localised with `ZoneInfo("Europe/Berlin")` rather than a fixed `+02:00`, so October's transition needs no second edit. `tz_localize` raises inside the ambiguous hour and the supplier exports around 03:00 local; I left it raising.
- No migration: the rows already in Postgres stay naive Berlin. Tonight's upsert overwrites the whole catalogue.

## TODO

- Tomas: the PR.
- Tomas: whether `/stock` should refuse to serve stock older than 36h instead of publishing a stale `as_of`. Your call, you wrote the API -- I have not touched `api/app.py`.
- Tomas: the `SFTP_DIR` -> `SUPPLIER_SFTP_DIR` rename is reverted. `/opt/deploy/inventory-sync.sh` passes `SFTP_DIR` in and sits in the deploy repo rather than ours (`git log` has you as sole author), so renaming on our side alone would leave the loader on the default `/srv/supplier` as a remote path and fail at fetch rather than at startup. I can redo it in one change with the deploy side, or leave it.
- Priya: ask Norvell whether the `Z` format is permanent or someone flipped a flag? And whether they can send us a changelog for export changes -- we should not be finding this out from the job dying. Worth putting in front of them: the change date, 2026-09-21, and that the column name and the value format moved together. The only notice was a newsletter last week, "api and export improvements", which I deleted unread.

Tonight at 02:30 is the first unattended run through the new code. The timer is unchanged, the override variable is cleared so it takes Wednesday's file, and a failure now mails the team list instead of Lukas.

## Additional notes

- Alerting: the `OnFailure=` unit did fire, both nights, and mailed `lukas.reinhard@`, who left in March, so alerting on this service has been dead since spring. Recipient is now `ops-inventory@norvell-group.example`, tested by triggering the failure unit directly rather than waiting for an import to fail, and the mail arrived.
- Pandas bump: the dependabot 2.2.3 -> 2.3.0 that merged Thursday is not the cause. Both versions fail on Monday's file and both succeed on Sunday's, so the variable is the file, not the library. Nothing to revert.
- Historic timestamps: every row stored before Monday is off by the local offset, two hours in summer and one in winter. It was invisible because the `as_of` we publish was wrong by the same amount, so the data was consistent with itself and inconsistent only with reality. New rows are UTC, so the table is mixed until tonight's upsert.
- Backfill: Monday and Tuesday were run by hand on `ops-1`, about 5m50 for each upsert, in line with the historical runtime. `IMPORT_FILE_DATE` is unset again (checked), so tonight's run will not re-import Monday. Spot-checked `NV-44812` against the raw CSV: quantities, cost and currency match, and the `as_of` matches the row's own timestamp with no offset applied.
- Declined: a validation layer at the import boundary, and splitting the 241-line `load.py`. Both buy a better failure message, not a faster repair, and the repair is always reading the new file and teaching the loader about it.
- `applymap` at `load.py:87` is deprecated and becomes an error in a future pandas major. Not today's failure, the values reach the parse intact. Unfixed.
- `ruff` flags TRY003 on the new error message. Left standing, the long message is the point of it.

Verdict:
Why:

### 14-D

Fixing the timestamps will not get those SKUs out of your 48h flag -- they really are older than 48 hours, and the naive value makes them look two hours _newer_ than they are, not _older_ (Berlin local is still an assumption; Priya is asking Norvell). Dropping them from the table is what gets them out.

> how many are those

Not counted yet. I can have the number this morning.

> do they get fixed at some point?

Not on their own. No migration written -- I skipped one yesterday.

I can shift the old rows by the offset, or delete the SKUs Norvell no longer exports (Tomas reviews either). Which do you want?

Verdict:
Why:

### 15-C

Subject: Stock export format change, 2026-09-21

Hi Dana,

We import your nightly stock export from `feeds.norvell-supply.net`, and I have three questions about the change in `stock_2026-09-21.csv.gz` (address from your export documentation).

Two things changed in that file at once: the column `updated` became `updated_at`, and the values went from `2026-09-20 03:14:00` to `2026-09-21T02:04:11Z`. That broke our import for two nights. It is fixed on our side and accepts both now, so there is nothing to change on yours.

- New format: is `updated_at` with `Z` permanent, or a flag someone flipped?
- Old values: were the `updated` timestamps Berlin local time?
- Changelog: is there one for the export, or can we get notice before it changes?

Thanks,
Alan

Verdict:
Why:
