Two things about the test suite changed today. Neither is going back.

- `make test` now needs the `svc-db` container up first. Without it every test
  fails during collection with `ConnectionRefusedError: [Errno 111] Connection
  refused` against 127.0.0.1:5432, which reads like a broken import rather than a
  missing container. `docker compose up -d svc-db` from the repo root starts it.
- The `seed` fixture in `tests/conftest.py` is function-scoped now, because tests
  were seeing each other's rows. The suite went from around 20 seconds to around
  70.

Make sure whoever works here next does not lose time to either.
