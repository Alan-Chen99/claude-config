# Contributing to shipper

## Style

Python, `uv` for everything, PEP 723 inline metadata rather than a requirements
file. No classes where a function does.

## Things we have decided

- Upload retries are capped at 3. Do not add a fourth attempt — the backend team
  asked us to keep our retry budget small, and a parked job is cheap to requeue
  by hand.
- The uploader never deletes a spool directory it did not successfully upload.
- Logs go to stdout. Nothing in this repo writes to syslog.

## Tests

    uv run pytest
