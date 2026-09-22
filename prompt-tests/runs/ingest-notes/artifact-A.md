# Ingest pipeline — operator notes

Loads the day's CSV drops into a SQLite warehouse. Four files:

| File               | Role                                                          |
| ------------------ | ------------------------------------------------------------- |
| `run.sh`           | Entry point: applies `schema.sql`, then runs `ingest.py`      |
| `ingest.py`        | Reads `<drop_dir>/*.csv`, appends each to its table           |
| `schema.sql`       | Table definitions (`CREATE TABLE IF NOT EXISTS`)              |
| `requirements.txt` | pandas + numpy, pinned                                        |

## Running it

```bash
export INGEST_DB=/path/to/warehouse.db
./run.sh /path/to/drops          # drop dir defaults to ./drops
```

Two hard requirements, both of which fail in confusing ways (see Traps):

- **`cwd` must be this directory.** `run.sh` opens `schema.sql` by relative path.
- **Always go through `run.sh`, never `python3 ingest.py` directly.**

A drop file maps to a table by filename stem via the `TABLES` dict in `ingest.py`.
Stems not in that dict are skipped with a note on stderr (`refunds.csv` → skipped).
The dict is an identity mapping, so it functions purely as an allowlist.

### Python version

`requirements.txt` pins `pandas==2.1.4` / `numpy==1.26.4`. **Neither publishes a
wheel for Python 3.14, which is this box's default `python3`.** Installing there
falls back to a source build that fails — there is no C++ compiler in the image.

Use Python 3.12:

```bash
uv venv --python 3.12 .venv && VIRTUAL_ENV=$PWD/.venv uv pip install -r requirements.txt
export PATH="$PWD/.venv/bin:$PATH"
```

Either keep the pins and stay on 3.12, or bump both to 3.14-compatible releases.
Don't leave it to resolve against the default interpreter.

## Traps

These are confirmed by running the code, not read off it. Ordered by how much
damage they do.

### 1. `line_items` silently lands in a shadow table (data loss, exit 0)

`TABLES` maps `line_items` → table `line_items`. `schema.sql` defines
`order_lines`. Nothing reconciles the two.

`to_sql(if_exists="append")` **creates a table when it is missing**, so a
`line_items.csv` drop creates a new all-TEXT, constraint-free `line_items` table
and leaves `order_lines` empty. The run exits 0 and logs nothing:

```
== line_items  rows=2   CREATE TABLE "line_items" ("order_id" TEXT, "sku" TEXT, "qty" TEXT, ...)
== order_lines rows=0   -- the real schema table, never written
```

Anything reading `order_lines` sees an empty table indefinitely. One-line fix —
point the dict at the schema name:

```python
"line_items": "order_lines",
```

Check for an existing shadow table before fixing; its rows need migrating, and
its `qty` is TEXT where `order_lines.qty` is INTEGER.

### 2. Bypassing `run.sh` destroys the schema silently

`ingest.py` never applies `schema.sql` — only `run.sh` does. Run `ingest.py`
directly against a fresh DB and pandas invents **every** table as all-TEXT with
no `NOT NULL` and **no `UNIQUE`**: exit 0, no warning, every constraint gone.

```
CREATE TABLE "orders" ("order_id" TEXT, "customer_id" TEXT, "total_cents" TEXT, ...)
```

Losing `UNIQUE` also disables the only thing stopping re-runs from doubling rows
(#3). A DB created this way cannot be repaired by applying `schema.sql` later —
`CREATE TABLE IF NOT EXISTS` sees the tables and no-ops. Rebuild from scratch.

### 3. Re-running is not idempotent

There is no upsert; every run appends. Two different behaviours:

- **Tables with `UNIQUE`** (`orders`, `customers`) — the second run dies with
  `IntegrityError: UNIQUE constraint failed`. Loud, but see #4.
- **Tables without it** (`order_lines`, and the shadow `line_items`) — rows
  **silently duplicate**. Three runs of one file produced 6 rows from 2, exit 0
  every time. This is the failure mode to watch for; nothing surfaces it.

If re-running a drop is a real requirement, that needs `INSERT ... ON CONFLICT`
and a real key on `order_lines` — not a patch at the call site.

### 4. A failed run leaves the database half-loaded

`conn.commit()` fires per 5000-row chunk, so a failure mid-file keeps every
chunk before it. A 6000-row file failing in chunk 2 left exactly 5000 rows
committed, exit 1. Re-running then hits #3 and fails immediately on chunk 1 —
recovery needs manual cleanup first.

Recovery (verified): every row carries `source_file`, so roll the file back and
re-run it.

```bash
python3 -c "import sqlite3,os,sys; c=sqlite3.connect(os.environ['INGEST_DB']); \
print('deleted', c.execute('DELETE FROM orders WHERE source_file=?', (sys.argv[1],)).rowcount); \
c.commit()" orders.csv
./run.sh /path/to/drops
```

(There is no `sqlite3` CLI in this image — use `python3`, whose stdlib `sqlite3`
is always present, or `nix shell nixpkgs#sqlite` if you want the shell.)

Do this for each table the failed run touched. Files are processed in sorted
order (`customers`, `line_items`, `orders`), so anything alphabetically after
the failure never loaded at all.

### 5. The retry loop does nothing useful

```python
except sqlite3.OperationalError:
    if attempt == MAX_RETRIES - 1:
        raise
```

No `sleep`, no backoff, no logging, and it catches *all* `OperationalError`, not
just lock contention. A permanent schema error retries 5 times in 7ms and then
raises anyway — measured. Lock contention is already handled by
`connect(timeout=30.0)`, which busy-waits inside a single attempt; the retries
add up to 4 more 30s waits on top of it.

It buys nothing and hides the error class. Either drop it or make it
lock-specific with actual backoff.

## Schema / typing notes

- CSVs are read with `dtype=str`. SQLite column affinity converts numeric-looking
  strings on the way in, so `orders.total_cents` lands as INTEGER — but only
  because the column is declared INTEGER. A non-numeric value is stored as TEXT
  in that same column with no error. Shadow tables (#1, #2) have no affinity at
  all and keep everything TEXT.
- CSV headers must match table columns **exactly**. An extra column raises
  `OperationalError: table orders has no column named extra_col` (after 5
  pointless retries). A missing `NOT NULL` column raises `IntegrityError`.
- `source_file` is set from the filename and overwrites any same-named CSV
  column. It is the only provenance/rollback handle — keep it.
- `order_lines` has no unique key and no index, and no foreign keys are declared
  anywhere.

## Memory

`pd.read_csv` loads each file **entirely** into memory; `CHUNK_ROWS` only batches
the inserts. Large drops are bounded by RAM (3 cores / no GPU on this host). If
drops outgrow memory, switch to `pd.read_csv(..., chunksize=...)` and drop the
manual `iloc` slicing.

## If you change this

The two one-line fixes (#1 `TABLES` mapping, #2 applying the schema inside
`ingest.py`) are worth doing before anything else — both cause silent wrong
results rather than errors. There are no tests; a change is verified by running
against a scratch `INGEST_DB` and inspecting `sqlite_master` to confirm no
shadow tables appeared:

```bash
python3 - <<'EOF'
import sqlite3, os
c = sqlite3.connect(os.environ['INGEST_DB'])
for (name,) in c.execute("select name from sqlite_master where type='table' order by name"):
    rows = c.execute(f'select count(*) from "{name}"').fetchone()[0]
    ddl = " ".join(c.execute("select sql from sqlite_master where name=?", (name,)).fetchone()[0].split())
    print(f"{rows:>8}  {ddl[:100]}")
EOF
```

A **quoted** table name in the emitted DDL (`CREATE TABLE "orders"` rather than
`CREATE TABLE orders`) means pandas created that table, not `schema.sql` — that
is the signature of traps #1 and #2.
