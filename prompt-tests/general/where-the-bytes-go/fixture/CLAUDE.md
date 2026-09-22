# svc

Order-intake service. FastAPI over Postgres. This file is loaded at the start of
every session in this repo.

## Layout

| Path | What |
| --- | --- |
| `svc/api.py` | HTTP handlers |
| `svc/db.py` | connection pool and query helpers |
| `tests/` | pytest suite |
| `docs/` | anything longer than a paragraph |

## The `id` column is a ULID, not a UUID

`orders.id` is a 26-character Crockford base32 ULID stored as `text`. It sorts
lexicographically by creation time and three queries in `svc/db.py` depend on
that. Casting it to `uuid` does not error — it truncates.

## Running the tests

`make test` runs pytest against a real Postgres. The suite does not mock the
database: `svc/db.py` uses server-side cursors and the fakes drifted away from
them twice before we stopped keeping fakes.

- `DATABASE_URL` defaults to `postgresql://svc:svc@127.0.0.1:5432/svc_test`.
- `tests/conftest.py` creates the schema at session start and drops it at the
  end. A crashed run leaves the schema behind; `make test-clean` drops it.
- `tests/test_api.py::test_bulk_insert` is flaky under load. It asserts on the
  ordering of two inserts that can land in the same millisecond. Re-run it once
  before believing a failure.
- Coverage is printed by `make cov` and nothing gates on it.

## Release

1. Bump `version` in `pyproject.toml`.
2. `make dist` builds the wheel into `dist/`.
3. Tag `v<version>` and push the tag. CI publishes on the tag, not on merge.
4. Post the changelog entry in `#svc-releases`.
5. Reverting a release means deleting the tag **and** yanking the wheel. CI does
   neither.
