# Ingest pipeline — operator notes

Loads a directory of daily CSV drops into a SQLite warehouse database.

```
run.sh [DROP_DIR]   # DROP_DIR defaults to ./drops
  └─ applies schema.sql to $INGEST_DB (CREATE TABLE IF NOT EXISTS, safe to repeat)
  └─ exec ingest.py DROP_DIR
        └─ for each *.csv whose stem is in TABLES: read whole file, append in 5000-row chunks
```

`INGEST_DB` (path to the database file) is required; `run.sh` refuses to start without it.
A drop file whose stem is not in `TABLES` is skipped with a message on stderr and exit 0.

## Running it

**The pinned dependencies do not install on this container's default Python 3.14.**
`numpy==1.26.4` ships no cp313 or cp314 wheels, so both 3.13 and 3.14 fall back to a
source build, which fails — there is no C++ compiler in the image. 3.12 has wheels and
installs in about a second. Use it:

```bash
uv venv --python 3.12 .venv
VIRTUAL_ENV=$PWD/.venv uv pip install -r requirements.txt
export PATH="$PWD/.venv/bin:$PATH"
export INGEST_DB=/path/to/warehouse.db
./run.sh ./drops
```

Run from the repository directory. `run.sh` opens `schema.sql` by relative path, so
invoking it from anywhere else dies with `FileNotFoundError: 'schema.sql'`.

Failures exit non-zero with a full traceback; nothing is swallowed.

## Verified behavior

Everything below was reproduced against a scratch database, not inferred from reading.

### `line_items` drops never reach the schema's table

`TABLES` maps `line_items` → `line_items`, but `schema.sql` defines `order_lines`.
`to_sql(if_exists="append")` creates a missing table, so a `line_items.csv` drop
auto-creates a second table with all-TEXT columns and no constraints, while
`order_lines` stays empty. Exit code 0, no warning.

```
line_items:  CREATE TABLE "line_items" ("order_id" TEXT, "sku" TEXT, "qty" TEXT, "source_file" TEXT)   -- 3 rows
order_lines: CREATE TABLE order_lines (... qty INTEGER NOT NULL ...)                                    -- 0 rows
```

Decide which name is authoritative before changing either side; the mismatch is the
reason the `qty INTEGER` and `NOT NULL` constraints have never been enforced.

### Re-running the same drop is not idempotent, and the two tables disagree on how

There is no upsert — every load is a plain append.

- `orders` and `customers` have `UNIQUE` constraints: a second run raises
  `sqlite3.IntegrityError: UNIQUE constraint failed: customers.customer_id` and exits 1.
- `line_items` (auto-created, unconstrained) has no constraint: three runs of the same
  file silently produced 9 rows from 3.

Files are processed in sorted order, so `customers.csv` fails first and masks the
duplication happening in `line_items`.

### A failed load leaves the database partially written

`conn.commit()` runs per 5000-row chunk, and nothing rolls back on failure. A 12001-row
`orders.csv` with a duplicate key in the third chunk committed **10000 rows** before
raising. Re-running after fixing the CSV then collides with those 10000 rows on the
`UNIQUE` constraint, so recovery is manual: truncate, or delete by `source_file` before
retrying. `load_one` stamps that column with the CSV's filename on every table, so
`DELETE FROM orders WHERE source_file = 'orders.csv'` undoes one file's partial load.

### The retry loop cannot retry anything useful

```python
except sqlite3.OperationalError:      # 5 attempts, no sleep between them
```

Instrumented: **5 attempts in 3.4 ms** — no backoff, so it cannot outlast any real lock.
It is also never reached by the case it appears to target: `sqlite3.connect(timeout=30.0)`
makes the driver wait out contention first. Held a genuine `BEGIN EXCLUSIVE` lock for 3 s
against a running ingest, and it blocked 2.46 s inside the driver, then committed and
exited 0 — the `except` branch never fired.

What the loop does catch is permanent schema errors — an unexpected CSV column raises
`OperationalError: table orders has no column named promo_code`, which is retried five
times and then re-raised unchanged.

Also note the retry re-sends a chunk that may have partially inserted, since there is no
rollback between attempts.

### `dtype=str` does not prevent type surprises

Values still pass through pandas' default NA sentinels and SQLite's type affinity:

| CSV value | Lands as | Outcome |
|---|---|---|
| `1500` | INTEGER 1500 | as intended |
| `12.75` | REAL 12.75 | **stored silently in `total_cents INTEGER NOT NULL`**, exit 0 |
| *(empty)* | NULL | `IntegrityError: NOT NULL constraint failed` |
| `N/A`, `NA`, `null`, `None` | NULL | same crash — `dtype=str` does **not** disable `na_values` |

The `12.75` row is the dangerous one: a cents column quietly holding a float, with a
successful exit code. SQLite's INTEGER affinity only converts when the conversion is
lossless, and nothing here validates what it declined to convert.

## Before you change it

- `CHUNK_ROWS` buys nothing for memory. `pd.read_csv` materializes the whole file first
  and the chunking only slices that frame. If drops get large, pass `chunksize=` to
  `read_csv` itself.
- `numpy` is pinned in `requirements.txt` but never imported directly; it is only
  pandas' dependency.
- `ingest.py` reads `INGEST_DB` from the environment itself and takes the drop directory
  as `sys.argv[1]`, so it runs standalone — but it does not apply `schema.sql`. Run
  against a fresh database it exits 0 having created *every* table as all-TEXT with no
  constraints at all:

  ```
  CREATE TABLE "orders" ("order_id" TEXT, "customer_id" TEXT, "placed_at" TEXT, "total_cents" TEXT, "source_file" TEXT)
  ```

  Always go through `run.sh` unless the schema is already applied. A warehouse built this
  way accepts duplicate keys and non-numeric totals without complaint.
- The `source_file` column is the only provenance recorded, and an existing `source_file`
  column in a CSV would be overwritten by the filename.

## Reproducing these findings

Run from the repository directory (see above). There is no `sqlite3` CLI in this image;
query through Python.

```bash
D=$(mktemp -d)
printf 'order_id,customer_id,placed_at,total_cents\no1,c1,2026-09-01T10:00:00Z,1500\n' > "$D/orders.csv"
printf 'customer_id,email\nc1,a@example.com\n'                                          > "$D/customers.csv"
printf 'order_id,sku,qty\no1,SKU-A,2\n'                                                 > "$D/line_items.csv"

export INGEST_DB="$D/wh.db"
./run.sh "$D"; echo "first  run exit=$?"    # 0
./run.sh "$D"; echo "second run exit=$?"    # 1, UNIQUE constraint failed: customers.customer_id

python3 -c "
import sqlite3, os
c = sqlite3.connect(os.environ['INGEST_DB'])
for (n,) in c.execute(\"select name from sqlite_master where type='table' order by name\"):
    print(n, c.execute(f'select count(*) from \\\"{n}\\\"').fetchone()[0])"
# order_lines 0  /  line_items 1  -> the table-name mismatch
```
