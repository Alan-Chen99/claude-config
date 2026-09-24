[09:10] user: import died again last night. priya says /stock is still showing sundays as_of

[09:11] user: journal from ops-1

```
Sep 23 02:30:04 ops-1 systemd[1]: Starting inventory-import.service - Supplier stock import...
Sep 23 02:30:05 ops-1 inventory-import[21714]: INFO  fetching sftp://feeds.norvell-supply.net/out/stock_2026-09-22.csv.gz
Sep 23 02:30:41 ops-1 inventory-import[21714]: INFO  downloaded 38.2 MB in 36.1s
Sep 23 02:30:42 ops-1 inventory-import[21714]: INFO  decompressed to /srv/supplier/stock_2026-09-22.csv
Sep 23 02:30:42 ops-1 inventory-import[21714]: INFO  parsing 411274 rows
Sep 23 02:30:44 ops-1 inventory-import[21714]: Traceback (most recent call last):
Sep 23 02:30:44 ops-1 inventory-import[21714]:   File "/opt/inventory-sync/import/load.py", line 114, in normalise
Sep 23 02:30:44 ops-1 inventory-import[21714]:     parsed = pd.to_datetime(df[ts_col], format=TS_FORMAT)
Sep 23 02:30:44 ops-1 inventory-import[21714]:   File "/opt/inventory-sync/.venv/lib/python3.11/site-packages/pandas/core/tools/datetimes.py", line 1067, in to_datetime
Sep 23 02:30:44 ops-1 inventory-import[21714]:     values = convert_listlike(arg._values, format)
Sep 23 02:30:44 ops-1 inventory-import[21714]: ValueError: unconverted data remains when parsing with format "%Y-%m-%d %H:%M:%S"
Sep 23 02:30:44 ops-1 inventory-import[21714]: The above exception was the direct cause of the following exception:
Sep 23 02:30:44 ops-1 inventory-import[21714]: Traceback (most recent call last):
Sep 23 02:30:44 ops-1 inventory-import[21714]:   File "/opt/inventory-sync/import/load.py", line 241, in <module>
Sep 23 02:30:44 ops-1 inventory-import[21714]:     main()
Sep 23 02:30:44 ops-1 inventory-import[21714]:   File "/opt/inventory-sync/import/load.py", line 118, in normalise
Sep 23 02:30:44 ops-1 inventory-import[21714]:     raise LoadError(f"could not parse timestamp column {ts_col!r}") from exc
Sep 23 02:30:44 ops-1 inventory-import[21714]: import.load.LoadError: could not parse timestamp column 'updated_at'
Sep 23 02:30:44 ops-1 systemd[1]: inventory-import.service: Main process exited, code=exited, status=1/FAILURE
Sep 23 02:30:44 ops-1 systemd[1]: inventory-import.service: Failed with result 'exit-code'.
```

[09:13] agent: Thank you. I will begin by reading the relevant portion of `import/load.py` so that I can see the exact parsing call and how `ts_col` and `TS_FORMAT` are determined, rather than reasoning from the traceback alone. Reading lines 90 through 130 of `import/load.py`.

```python
TS_PREFIX = "updated"
TS_FORMAT = "%Y-%m-%d %H:%M:%S"

def normalise(df: pd.DataFrame) -> pd.DataFrame:
    df.columns = [c.strip().lower() for c in df.columns]
    try:
        ts_col = next(c for c in df.columns if c.startswith(TS_PREFIX))
    except StopIteration as exc:
        raise LoadError("no timestamp column") from exc
    try:
        parsed = pd.to_datetime(df[ts_col], format=TS_FORMAT)
    except Exception as exc:
        raise LoadError(f"could not parse timestamp column {ts_col!r}") from exc
    df["updated"] = parsed
    return df
```

Two observations. The column is located by prefix match rather than exact name, which is a loose contract with the supplier. And the `except Exception` wrapper discards the underlying pandas message, so the journal shows the format that failed but not the value that failed against it — the piece of evidence I would most like to have.

[09:16] user: hm. so what broke

[09:17] agent: I do not yet know, and I would rather not guess ahead of the evidence. The plausible candidates are a change in the supplier's file, a change in our parsing dependency, or an environment change on `ops-1`. "Unconverted data remains" means the string began matching the format and then had trailing characters left over, which narrows it somewhat.

[09:18] user: dependabot merged a pandas bump thursday. 2.2.3 -> 2.3.0. check that first

[09:19] agent: Understood, I will take that first — pandas has been tightening `to_datetime` across the 2.x line, and a stricter parse would fit a job that worked Sunday and failed Monday. Building an isolated virtualenv with pandas pinned back to 2.2.3, then running the loader against Monday's file in dry-run mode so nothing touches Postgres.

```
$ uv venv /tmp/pin223 --python 3.11
Using CPython 3.11.9
Creating virtual environment at: /tmp/pin223
$ uv pip install --python /tmp/pin223/bin/python -r requirements.txt "pandas==2.2.3"
Resolved 34 packages in 611ms
Installed 34 packages in 1.82s
 + pandas==2.2.3
 + numpy==1.26.4
 ...
```

[09:24] agent: Running the loader against Monday's file, `/srv/supplier/stock_2026-09-21.csv`, with `--dry-run`.

```
$ /tmp/pin223/bin/python -m import.load --file /srv/supplier/stock_2026-09-21.csv --dry-run
INFO  parsing 410883 rows
/opt/inventory-sync/import/load.py:87: FutureWarning: DataFrame.applymap has been deprecated. Use DataFrame.map instead.
  df = df.applymap(lambda v: v.strip() if isinstance(v, str) else v)
ERROR could not parse timestamp column 'updated_at'
```

[09:26] agent: The failure reproduces under pandas 2.2.3. Before I draw a conclusion, I want to flag the `FutureWarning` on line 87: `DataFrame.applymap` is deprecated. That is a separate latent problem which will become an error in a future major version, and it is in the same function family as the failure.

[09:27] user: is that the thing?

[09:28] agent: I should check rather than assume. `applymap` is deprecated but functional, and it runs before the timestamp parse, so it cannot be the cause unless it is mangling the values. Dumping the first three values of `updated_at` immediately after that line.

```
$ /tmp/pin223/bin/python -c "..."
'2026-09-21T02:04:11Z'
'2026-09-21T02:04:11Z'
'2026-09-21T02:04:11Z'
```

[09:31] agent: The warning is unrelated. The values arrive intact and are stripped correctly. I retract it as a lead; it is worth fixing eventually but it is not today's failure.

[09:33] user: ok and the pin?

[09:34] agent: The pin does not help. To compare two measurements rather than one measurement against a memory, I ran the same files through a second virtualenv holding 2.3.0.

```
$ /tmp/pin230/bin/python -m import.load --file /srv/supplier/stock_2026-09-21.csv --dry-run
INFO  parsing 410883 rows
ERROR could not parse timestamp column 'updated_at'
$ /tmp/pin223/bin/python -m import.load --file /srv/supplier/stock_2026-09-20.csv --dry-run
INFO  parsing 410402 rows
INFO  dry run, 410402 rows normalised, as_of=2026-09-20 03:14:00
$ /tmp/pin230/bin/python -m import.load --file /srv/supplier/stock_2026-09-20.csv --dry-run
INFO  parsing 410402 rows
INFO  dry run, 410402 rows normalised, as_of=2026-09-20 03:14:00
```

Both pandas versions succeed on Sunday's file and both fail on Monday's. The variable is the file, not the library. I was wrong to spend the morning on the dependency, and the dependabot bump is exonerated.

[09:46] user: fine. so whats different in the file

[09:47] agent: Comparing the header lines directly.

```
$ head -1 /srv/supplier/stock_2026-09-20.csv
sku,description,warehouse,qty_on_hand,qty_reserved,unit_cost,currency,updated
$ head -1 /srv/supplier/stock_2026-09-21.csv
sku,description,warehouse,qty_on_hand,qty_reserved,unit_cost,currency,updated_at
$ head -1 /srv/supplier/stock_2026-09-22.csv
sku,description,warehouse,qty_on_hand,qty_reserved,unit_cost,currency,updated_at
```

And the first data row of each, for the same SKU, which happens to sort first in both files.

```
--- /srv/supplier/stock_2026-09-20.csv
+++ /srv/supplier/stock_2026-09-21.csv
-NV-44812,"Hex bolt M8x40 zinc",WH2,1840,120,0.1400,EUR,2026-09-20 03:14:00
+NV-44812,"Hex bolt M8x40 zinc",WH2,1792,96,0.1400,EUR,2026-09-21T02:04:11Z
```

[09:52] user: ohhh

[09:52] user: they sent a newsletter last week. "api and export improvements". i deleted it

[09:54] agent: That reconciles everything, and I want to restate it carefully, because two distinct changes landed in the same file and it would be easy to fix only one.

The supplier renamed the column from `updated` to `updated_at`. Our prefix match absorbed that change silently — `"updated_at".startswith("updated")` is true — so the rename did not break us on its own, and that is why the traceback reported the new name while we were still looking for a dependency problem. I will note that the string `'updated_at'` was in the journal excerpt you pasted at 09:10 and I did not attend to it; had I done so we would have arrived here two hours earlier.

The second change is the one that broke us. The value format moved from `2026-09-20 03:14:00` to `2026-09-21T02:04:11Z`. Our format string consumes `2026-09-21` and then finds `T02:04:11Z` where it expected a space, which is precisely the "unconverted data remains" message.

There is a semantic change hiding inside the format change, and it matters more than either. The old values carried no zone. Sunday's row says `03:14:00`, Monday's says `02:04:11Z`. Those are roughly the same wall-clock moment if the old values were supplier-local: Germany is on CEST in September, UTC+2, so an export running at about 04:00 local would be about 02:00 UTC. The supplier is in Bremen, so the old column was almost certainly Europe/Berlin local time and we have been storing it naive, as if it were UTC, all along.

[10:01] user: so weve been 2h off forever

[10:02] agent: In summer, yes. In winter it would have been one hour, since CET is UTC+1. The error was invisible because the `as_of` we publish was wrong by the same offset as the row timestamps, so the two were consistent with each other and inconsistent only with reality.

[10:05] user: ok. fix it so it takes both

[10:06] agent: Before I write anything, I would like to put a larger option in front of you, because this is the second time the supplier has moved something under us and I suspect it will not be the last.

Rather than patching the timestamp handling alone, I would propose introducing a validation layer at the import boundary: a pydantic model describing every column we consume — `sku`, `description`, `warehouse`, `qty_on_hand`, `qty_reserved`, `unit_cost`, `currency`, and the timestamp — with explicit types, an alias per column so renames are declarative, and a validator per field. The import would then reject a malformed file at row zero with a precise field-level message, instead of failing somewhere in the middle of `normalise` with whatever error the underlying library happens to raise. It would also give us a single place to record what we believe the supplier's contract to be, which is currently spread across the parsing code as implicit assumptions.

[10:11] user: no

[10:11] user: they change the export like twice a year. that just fails earlier and we still have to go read the csv and fix it by hand

[10:12] agent: That is a fair objection and I accept it. The layer would improve the failure message but not the time to repair, since the repair is always "read the new file and teach the loader about it" — and it would add a second place to edit each time. Withdrawn.

I will do the narrow thing instead: accept either column name, accept either value format, store UTC, and make the failure message useful when neither column is present by including the actual header line.

[10:14] user: yeah. tests too, one row of each

[10:16] agent: Implementing now in `import/load.py`. The change replaces the prefix match with an explicit ordered list of accepted names, and replaces the single format string with a two-branch parse keyed on the shape of the value.

```python
TS_COLUMNS = ("updated_at", "updated")
TS_FORMAT_NAIVE = "%Y-%m-%d %H:%M:%S"
SUPPLIER_TZ = ZoneInfo("Europe/Berlin")

def parse_timestamps(values: pd.Series) -> pd.Series:
    sample = values.dropna().iloc[0] if len(values.dropna()) else ""
    if sample.endswith("Z") or "T" in sample:
        return pd.to_datetime(values, format="ISO8601", utc=True)
    naive = pd.to_datetime(values, format=TS_FORMAT_NAIVE)
    return naive.dt.tz_localize(SUPPLIER_TZ).dt.tz_convert("UTC")

def normalise(df: pd.DataFrame) -> pd.DataFrame:
    df.columns = [c.strip().lower() for c in df.columns]
    ts_col = next((c for c in TS_COLUMNS if c in df.columns), None)
    if ts_col is None:
        raise LoadError(
            "no supplier timestamp column; expected one of "
            f"{TS_COLUMNS}, header was: {','.join(df.columns)}"
        )
    df["updated"] = parse_timestamps(df[ts_col])
    return df
```

[10:29] agent: Two notes on choices you may want to overrule. I detect the format from the first non-null value rather than per row, so a file mixing both would be misparsed; a per-row branch over 410,000 rows seemed the worse trade, but say the word and I will change it. And I localise with `ZoneInfo("Europe/Berlin")` rather than a fixed `+02:00`, so October's transition needs no second edit — which does mean `tz_localize` will raise on the ambiguous hour, and the supplier exports at about 03:00 local, inside that window. I have left it raising rather than guessing.

[10:35] user: leave it raising. what about the rows already in pg

[10:36] agent: They stay as stored, naive and effectively Europe/Berlin, while new rows will be UTC, so the table is internally inconsistent until the old rows are replaced. I can write a one-off migration shifting them by the correct offset.

[10:38] user: no. every row gets overwritten tonight anyway

[10:38] agent: Agreed, the nightly upsert covers the whole catalogue, so the inconsistency has a lifetime of hours. Skipping the migration.

[10:41] agent: Tests added to `tests/test_load.py`: one row in each format, plus a header with neither column to pin the error message.

```python
def test_old_format_is_berlin_local():
    df = _frame("updated", "2026-09-20 03:14:00")
    assert normalise(df)["updated"][0] == pd.Timestamp("2026-09-20T01:14:00Z")

def test_new_format_is_utc():
    df = _frame("updated_at", "2026-09-21T02:04:11Z")
    assert normalise(df)["updated"][0] == pd.Timestamp("2026-09-21T02:04:11Z")

def test_missing_column_reports_header():
    df = _frame("last_changed", "2026-09-21T02:04:11Z")
    with pytest.raises(LoadError) as exc:
        normalise(df)
    assert "last_changed" in str(exc.value)
```

```
$ pytest tests/test_load.py -q
.......                                                     [100%]
7 passed in 1.42s
```

[10:52] agent: All seven pass, including the four that existed before. For completeness I will restate what now happens end to end, since the behaviour has changed in three places. The loader looks for `updated_at` first and `updated` second, taking whichever it finds. If the values look ISO 8601 it parses them as UTC and keeps them as UTC. If they look like the old naive format it parses them, attaches Europe/Berlin, and converts to UTC. In both branches the column written to Postgres is UTC. If neither column name appears, it raises immediately with the full header line in the message, so the next time the supplier renames something the journal will tell us what they renamed it to without anyone having to go and open the CSV.

[10:56] user: ok

[10:57] agent: One further thing from the linter, which I raise as a question rather than acting on it. `ruff` flags the new error message:

```
import/load.py:104:15: TRY003 Avoid specifying long messages outside the exception class
Found 1 error.
```

The idiomatic resolution is to move the message construction into `LoadError` itself, taking the header as an argument. I can do that, or add a `noqa`, or change nothing and let the warning stand.

[11:02] user: leave it. the message is the whole point

[11:02] agent: Leaving it as written, warning and all.

[12:58] user: back. lets get the two nights in

[13:00] agent: I will deploy first, then backfill. Pulling the branch on `ops-1` and confirming the working tree matches what we tested.

```
$ ssh ops-1 'cd /opt/inventory-sync && git pull --ff-only && git rev-parse --short HEAD'
Updating 4b1e7ac..d0f9e22
Fast-forward
 import/load.py       | 31 +++++++++++++++++++------------
 tests/test_load.py   | 24 ++++++++++++++++++++++++
d0f9e22
```

[13:04] agent: The unit takes the file date from `IMPORT_FILE_DATE`, defaulting to yesterday when unset. Since the service is started by systemd rather than a shell, I will set that in the manager environment and unset it afterwards — if it were left set, tonight's 02:30 run would re-import Monday's file.

```
$ ssh ops-1 'sudo systemctl set-environment IMPORT_FILE_DATE=2026-09-21 && sudo systemctl start inventory-import'
```

[13:11] agent: Running. Following the journal.

```
Sep 23 13:05:12 ops-1 inventory-import[48122]: INFO  using local file /srv/supplier/stock_2026-09-21.csv
Sep 23 13:05:12 ops-1 inventory-import[48122]: INFO  parsing 410883 rows
Sep 23 13:05:54 ops-1 inventory-import[48122]: INFO  parsed 410883 rows in 41.8s
Sep 23 13:11:39 ops-1 inventory-import[48122]: INFO  upserted 410883 rows (inserted 318, updated 410565) in 5m45s
Sep 23 13:11:39 ops-1 inventory-import[48122]: INFO  as_of=2026-09-21T02:04:11+00:00
Sep 23 13:11:40 ops-1 systemd[1]: inventory-import.service: Deactivated successfully.
```

[13:12] agent: Monday is in. Five minutes forty-five for the upsert, which is in line with the historical runtime. Starting Tuesday.

```
$ ssh ops-1 'sudo systemctl set-environment IMPORT_FILE_DATE=2026-09-22 && sudo systemctl start inventory-import'
```

```
Sep 23 13:19:47 ops-1 inventory-import[48331]: INFO  upserted 411274 rows (inserted 402, updated 410872) in 5m52s
Sep 23 13:19:47 ops-1 inventory-import[48331]: INFO  as_of=2026-09-22T02:07:38+00:00
Sep 23 13:19:48 ops-1 systemd[1]: inventory-import.service: Deactivated successfully.
```

```
$ ssh ops-1 'sudo systemctl unset-environment IMPORT_FILE_DATE && sudo systemctl show-environment | grep -c IMPORT_FILE_DATE'
0
```

[13:21] agent: Both nights loaded and the override is cleared. Checking the API.

```
$ curl -s https://inventory.internal/stock?warehouse=WH2 | head -c 200
{"as_of":"2026-09-22T02:07:38Z","count":118402,"items":[{"sku":"NV-44812","qty_on_hand":1784,"qty_reserved":88,...
```

[13:24] user: hm thats monday

[13:25] agent: It is Tuesday. 2026-09-22 is Tuesday; Sunday, which is what `/stock` was serving this morning, was 2026-09-20. The value is also UTC, marked by the trailing `Z`, so in local terms that export was taken at 04:07 on Tuesday morning.

[13:26] user: right. ok

[13:31] user: checking a sku by hand

```
$ grep '^NV-44812,' /srv/supplier/stock_2026-09-22.csv
NV-44812,"Hex bolt M8x40 zinc",WH2,1784,88,0.1400,EUR,2026-09-22T02:07:38Z
$ curl -s 'https://inventory.internal/stock?sku=NV-44812'
{"as_of":"2026-09-22T02:07:38Z","count":1,"items":[{"sku":"NV-44812","warehouse":"WH2","qty_on_hand":1784,"qty_reserved":88,"unit_cost":"0.1400","currency":"EUR"}]}
```

[13:33] user: good thats the file

[13:34] agent: Quantities, cost and currency match the row, and the `as_of` matches the row's own timestamp with no offset applied, which is correct for the new format.

[14:06] user: who was supposed to get the alert monday. nobody said anything

[14:08] agent: Reading the failure unit.

```
$ ssh ops-1 'systemctl cat inventory-import-failure@.service'
# /etc/systemd/system/inventory-import-failure@.service
[Unit]
Description=Mail alert for failed %i

[Service]
Type=oneshot
ExecStart=/usr/local/bin/unit-status-mail lukas.reinhard@norvell-group.example %i
```

The `OnFailure=` in `inventory-import.service` points here, so the alert did fire — twice, once per night — and was mailed to `lukas.reinhard@`.

[14:10] user: lukas left in march

[14:11] agent: Then the alerting has been silently non-functional since spring, and the two nights of failure were not unobserved by the system, only unobserved by anyone still on the team. Changing the recipient to the team list. Please confirm the address is `ops-inventory@norvell-group.example`.

[14:12] user: yes that one

[14:14] agent: Edited, reloaded, and tested by triggering the failure unit directly so that no real import had to fail to prove it.

```
$ ssh ops-1 'sudo systemctl daemon-reload && sudo systemctl start inventory-import-failure@selftest.service'
$ ssh ops-1 'journalctl -u inventory-import-failure@selftest -n 3 --no-pager'
Sep 23 14:13:58 ops-1 unit-status-mail[49610]: sent to ops-inventory@norvell-group.example (subject: [ops-1] selftest)
Sep 23 14:13:58 ops-1 systemd[1]: inventory-import-failure@selftest.service: Deactivated successfully.
```

[14:16] user: got it in my inbox

[14:40] user: while youre in there rename SFTP_DIR to SUPPLIER_SFTP_DIR pls. its too vague

[14:42] agent: Searching the repository for the name before changing anything.

```
$ grep -rn 'SFTP_DIR' --include='*.py' --include='*.env' --include='*.service' --include='*.md' .
import/load.py:23:SFTP_DIR = os.environ.get("SFTP_DIR", "/srv/supplier")
import/fetch.py:41:    remote = f"{SFTP_DIR}/stock_{date}.csv.gz"
docs/operations.md:64:| `SFTP_DIR` | remote export directory | `/out` |
deploy/inventory-import.service:11:Environment=SFTP_DIR=/out
```

Four occurrences, all ours. Renamed in all four, tests still pass. Before you commit it I want to widen the search beyond the repository, because an environment variable is an interface and we are only one side of it.

[14:49] agent: That was worth doing.

```
$ ssh ops-1 'grep -rn "SFTP_DIR" /opt/deploy/ 2>/dev/null'
/opt/deploy/inventory-sync.sh:38:  SFTP_DIR="${SFTP_DIR:-/out}"
/opt/deploy/inventory-sync.sh:52:    --env SFTP_DIR="$SFTP_DIR" \
```

`/opt/deploy/inventory-sync.sh` is not in our repository. `git log` on the deploy repo shows Tomas as the sole author, most recently three weeks ago. If we rename on our side without a matching change there, the deploy would pass `SFTP_DIR`, our loader would not see `SUPPLIER_SFTP_DIR`, and it would fall back to the default `/srv/supplier` as a remote path, which would fail at fetch time rather than at startup.

[14:52] user: ugh. revert it

[14:53] agent: Reverted.

```
$ git checkout -- import/load.py import/fetch.py docs/operations.md deploy/inventory-import.service
$ git diff --stat
 import/load.py     | 31 +++++++++++++++++++------------
 tests/test_load.py | 24 ++++++++++++++++++++++++
```

The only changes remaining in the working tree are the timestamp fix and its tests. The rename is entirely gone, including from the docs table.

[15:08] agent: A structural observation, offered only because I have now read the whole file. `import/load.py` is 241 lines and does four separable things: fetch orchestration, CSV parsing, normalisation, and the upsert. Splitting it would make each testable without a database, and would have made this morning's reproduction a two-line test instead of a virtualenv. An hour, plus review.

[15:10] user: no. not today and probably not ever

[15:11] agent: Withdrawn.

[15:26] user: put the two formats in operations.md so the next person doesnt do what i did this morning

[15:29] agent: Added under the existing "Supplier export" section in `docs/operations.md`.

```markdown
The timestamp column has appeared under two names and in two formats.

| Header | Example | Interpretation |
| --- | --- | --- |
| `updated` | `2026-09-20 03:14:00` | Europe/Berlin local, no zone marker |
| `updated_at` | `2026-09-21T02:04:11Z` | UTC, ISO 8601 |

The loader accepts either and stores UTC. It selects the format from the first
non-null value in the file, so a file mixing both would be misparsed. The change
arrived without notice on 2026-09-21 and broke that night's and the following
night's import.
```

[15:34] user: good. commit and push

[15:36] agent: Committed and pushed to `fix/supplier-timestamp-formats`, with the pull request opened against `main`.

```
$ git commit -m "load: accept both supplier timestamp columns and formats" -m "Supplier renamed 'updated' to 'updated_at' and switched from naive local time to ISO 8601 UTC on 2026-09-21. Accept either, store UTC, and include the header line when neither column is present."
[fix/supplier-timestamp-formats d0f9e22] load: accept both supplier timestamp columns and formats
 3 files changed, 71 insertions(+), 14 deletions(-)
$ git push -u origin fix/supplier-timestamp-formats
remote: Create a pull request: https://git.internal/ops/inventory-sync/pull/new/fix/supplier-timestamp-formats
```

[15:40] user: ill ask tomas to look at it tomorrow

[17:12] user: ill message priya to ask the supplier if the Z thing is permanent or if someone flipped a flag

[17:12] user: and whether they can send us a changelog for exports. we shouldnt find this out from the job dying

[17:14] agent: Noted. If it is useful to her, the two facts worth putting in front of the supplier are the exact date the format changed, 2026-09-21, and that the change was simultaneous in both the column name and the value format, which suggests a deliberate release rather than drift.

[17:20] user: the 36h thing. whether /stock should just refuse to serve stuff older than 36h instead of showing a stale as_of

[17:21] user: thats tomas call, he wrote the api. not doing it myself

[17:22] agent: Understood, I will not touch `api/app.py`.

[17:30] user: tonight 0230 is the first run that goes through the new code on its own

[17:31] agent: Yes. The timer is unchanged and still `OnCalendar=*-*-* 02:30:00`, the override variable is cleared so it will take Wednesday's file by default, and if it fails the alert now reaches the team list rather than Lukas.

[17:38] user: ok im off. laters
