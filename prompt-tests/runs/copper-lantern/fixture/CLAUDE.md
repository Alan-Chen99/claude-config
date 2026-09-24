# spool

Keeps build artifacts on disk with an index, and drops the old ones.

## Conventions

- Retention is a whole number of days; `spool prune` takes `--days N`.
- Timestamps are UTC ISO 8601 strings, never epoch seconds.
- Artifact ids are opaque; never parse one.

## Build and test

```bash
python -m pytest -q
```
