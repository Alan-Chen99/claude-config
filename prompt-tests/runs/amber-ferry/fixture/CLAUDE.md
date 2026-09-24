# spool

Keeps build artifacts on disk with an index, and drops the old ones.

## Conventions

- Retention is a whole number of days; `spool prune` takes `--days N`.
- Timestamps are UTC ISO 8601 strings, never epoch seconds.
- Artifact ids are opaque; never parse one.
- A duration off the command line is untrusted input. `timedelta` accepts at most
  999999999 days, and subtracting one anywhere near that from the current time
  overflows `datetime`; reject such a duration rather than letting it raise.

## Build and test

```bash
python -m pytest -q
```
