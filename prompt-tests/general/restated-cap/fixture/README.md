# shipper

Moves finished render jobs from the worker pool to object storage.

## How it works

A worker writes its output to `/var/spool/shipper/<job-id>/`. The shipper picks
the directory up, tars it, and uploads the tarball to the `renders` bucket. On a
failed upload it retries up to 3 times with exponential backoff, then parks the
job in `/var/spool/shipper/parked/` for an operator to look at.

## Running it

    uv run uploader/retry.py --spool /var/spool/shipper

## Configuration

| Env var | Default | What |
| --- | --- | --- |
| `SHIPPER_BUCKET` | `renders` | Destination bucket |
| `SHIPPER_SPOOL` | `/var/spool/shipper` | Spool root |
| `SHIPPER_TIMEOUT` | `30` | Per-attempt upload timeout, seconds |
