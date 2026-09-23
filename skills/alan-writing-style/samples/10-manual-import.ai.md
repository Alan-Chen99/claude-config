## Running the import by hand

The nightly timer starts `inventory-import.service` at 02:30 (`OnCalendar=*-*-* 02:30:00`) and imports yesterday's supplier file. You will need to run it by hand when a night has failed and has to be backfilled, or when you want to re-import a particular day.

### Pin the file date

The unit takes the date of the file to import from `IMPORT_FILE_DATE`, and defaults to yesterday when that is unset. The date is the one in the filename, `/srv/supplier/stock_<date>.csv`, which is the day the supplier's export covers.

Because the service is started by systemd rather than from your shell, exporting the variable in your session does nothing. It has to be set in the manager environment:

```
$ ssh ops-1 'sudo systemctl set-environment IMPORT_FILE_DATE=2026-09-21 && sudo systemctl start inventory-import'
```

If the decompressed CSV is already in `/srv/supplier` the run uses it instead of fetching over SFTP again, and says so:

```
Sep 23 13:05:12 ops-1 inventory-import[48122]: INFO  using local file /srv/supplier/stock_2026-09-21.csv
```

### Clear the override afterwards

This is the step that bites. A value left in the manager environment stays there, so the next 02:30 run would re-import the day you pinned rather than the night that has just arrived. Unset it as soon as the run you wanted is finished, and check that it is gone:

```
$ ssh ops-1 'sudo systemctl unset-environment IMPORT_FILE_DATE && sudo systemctl show-environment | grep -c IMPORT_FILE_DATE'
0
```

### Follow the run

The unit is `Type=oneshot` in effect — it exits when the import is done — so watch the journal rather than the exit of `systemctl start`:

```
$ ssh ops-1 'journalctl -u inventory-import -f'
Sep 23 13:05:12 ops-1 inventory-import[48122]: INFO  parsing 410883 rows
Sep 23 13:05:54 ops-1 inventory-import[48122]: INFO  parsed 410883 rows in 41.8s
Sep 23 13:11:39 ops-1 inventory-import[48122]: INFO  upserted 410883 rows (inserted 318, updated 410565) in 5m45s
Sep 23 13:11:39 ops-1 inventory-import[48122]: INFO  as_of=2026-09-21T02:04:11+00:00
Sep 23 13:11:40 ops-1 systemd[1]: inventory-import.service: Deactivated successfully.
```

For a full catalogue of roughly 411,000 rows, expect about 40 seconds to parse and between five and six minutes for the upsert. Anything much longer than that is worth looking into.

The `as_of` line is the timestamp carried by the rows themselves, in UTC, so it reports when the supplier took the export and not when you ran the import.

### Backfilling more than one night

Run one day at a time and in order, oldest first, each with its own `set-environment` and `start`. The upsert covers the whole catalogue, so a later day overwrites an earlier one and out-of-order runs leave you with stale quantities. Wait for `Deactivated successfully` before starting the next day; two concurrent imports both upserting every SKU is not something to find out about.

### Check what landed

The API reports the `as_of` of the newest import:

```
$ curl -s https://inventory.internal/stock?warehouse=WH2 | head -c 200
{"as_of":"2026-09-22T02:07:38Z","count":118402,"items":[{"sku":"NV-44812","qty_on_hand":1784,"qty_reserved":88,...
```

Read that date carefully. It is the day the export covers, not the day you ran the import, and it is UTC — the trailing `Z` — so an export taken at 04:07 Bremen time in summer appears as `02:07:38Z`.

To confirm the numbers and not just the date, pick a SKU out of the CSV and compare it against the API:

```
$ grep '^NV-44812,' /srv/supplier/stock_2026-09-22.csv
NV-44812,"Hex bolt M8x40 zinc",WH2,1784,88,0.1400,EUR,2026-09-22T02:07:38Z
$ curl -s 'https://inventory.internal/stock?sku=NV-44812'
{"as_of":"2026-09-22T02:07:38Z","count":1,"items":[{"sku":"NV-44812","warehouse":"WH2","qty_on_hand":1784,"qty_reserved":88,"unit_cost":"0.1400","currency":"EUR"}]}
```

Quantities, cost and currency should match the row, and `as_of` should match the row's own timestamp with no offset applied.

### If you are running by hand because the nightly job failed

Confirm `ops-1` is on the code you think it is on before you start, particularly if a fix was merged for the failure you are backfilling:

```
$ ssh ops-1 'cd /opt/inventory-sync && git pull --ff-only && git rev-parse --short HEAD'
```

Failures of the nightly run are mailed by `inventory-import-failure@.service` to `ops-inventory@norvell-group.example`. You can test that path without failing a real import by starting the failure unit directly:

```
$ ssh ops-1 'sudo systemctl start inventory-import-failure@selftest.service'
```
