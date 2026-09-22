# ledger-sync

Moves settled rows out of `queue/` and into the vendor's ingest API.

## Layout

| Path | What |
| --- | --- |
| `sync.sh` | The push loop. Cron runs it every ten minutes. |
| `pack.py` | Groups queued `*.json` into one payload per call. |
| `queue/` | Pending rows, one file each. Written by the settlement job. |

## Running it

`VENDOR_TOKEN` comes from the ops vault. `./sync.sh` is idempotent — a row that
posts twice is deduplicated on their side by `row_id`.
