## Manual import

The nightly timer (`OnCalendar=*-*-* 02:30:00`) starts `inventory-import.service` on `ops-1` and imports yesterday's file, `/srv/supplier/stock_<date>.csv`. For another day, set `IMPORT_FILE_DATE` in the manager environment rather than your shell:

```
$ ssh ops-1 'sudo systemctl set-environment IMPORT_FILE_DATE=2026-09-21 && sudo systemctl start inventory-import'
$ ssh ops-1 'journalctl -u inventory-import -f'
```

Clear it when the run is done -- a value left set means tonight's 02:30 run re-imports that day instead of the night that just arrived:

```
$ ssh ops-1 'sudo systemctl unset-environment IMPORT_FILE_DATE && sudo systemctl show-environment | grep -c IMPORT_FILE_DATE'
0
```

- Runtime: about 40s to parse and 5-6 minutes to upsert a full catalogue of ~411,000 rows, measured on the 2026-09-21 and 2026-09-22 backfills.
- Several nights: one day at a time, oldest first, and wait for `Deactivated successfully` before the next. The upsert covers the whole catalogue, so a later day overwrites an earlier one.
- Local file: a decompressed CSV already in `/srv/supplier` is used instead of a fresh SFTP fetch, and the journal says `using local file`.
- After a failure: `cd /opt/inventory-sync && git pull --ff-only` on `ops-1` first, so the backfill runs the fix rather than the code that failed.
- Failure alert: a failed run mails `ops-inventory@norvell-group.example` through `inventory-import-failure@.service`. Starting `inventory-import-failure@selftest.service` tests that path without failing an import.
- `as_of`: the timestamp the rows carry, in UTC, so it names the export the supplier took and not the day you ran the import (see "Supplier export" for the two formats).

Spot-check a SKU against the file:

```
$ grep '^NV-44812,' /srv/supplier/stock_2026-09-22.csv
NV-44812,"Hex bolt M8x40 zinc",WH2,1784,88,0.1400,EUR,2026-09-22T02:07:38Z
$ curl -s 'https://inventory.internal/stock?sku=NV-44812'
{"as_of":"2026-09-22T02:07:38Z","count":1,"items":[{"sku":"NV-44812","warehouse":"WH2","qty_on_hand":1784,"qty_reserved":88,"unit_cost":"0.1400","currency":"EUR"}]}
```
