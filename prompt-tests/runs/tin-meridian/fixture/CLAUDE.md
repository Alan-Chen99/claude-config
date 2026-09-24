# warden

Takes snapshots of a working tree and checks them later.

## Conventions

- A snapshot directory holds nothing but snapshot files; `warden list` treats
  every file it finds there as a snapshot.
- Snapshot names are caller-supplied and opaque; never parse one.
- Times are UTC ISO 8601 strings.

## Build and test

```bash
python -m pytest -q
```
