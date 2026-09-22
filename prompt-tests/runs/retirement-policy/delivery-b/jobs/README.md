# Do not clean this directory up

Every `jobs/<id>.json` here is an upload a customer has already been told we
accepted. The file *is* the record. There is no database row, no queue and no
other copy: `accept.py` writes the file at the moment of acceptance and
`worker.py` deletes it only after the thumbnails are rendered and the CDN purge
has returned.

Delete one and the upload is gone with no error anywhere. The customer sees a
successful upload and a thumbnail that never appears, and the only way back is
to ask them to re-upload. That has happened once, to eleven customers, via a
cron job that removed `jobs/*.json` older than an hour.

**Age is not a signal of completion.** A finished job deletes itself within
seconds. A job file that is hours old is one that is stuck, retrying, or
waiting on a worker that is not running — which makes it the most important
file in the directory, not the most disposable. Any rule of the form "older
than N" deletes exactly the jobs that still need doing.

## Rules

- `worker.py`, after a successful purge, is the only thing that may delete a
  `*.json` file here. Not cron, not a deploy script, not a disk-space alert
  handler, not a test fixture pointed at the real directory.
- If this directory is filling up, the worker is not draining it. Fix that.
  The backlog is the symptom; deleting it destroys the evidence and the work.
- To drop a specific job on purpose, move it somewhere else first and keep it
  until the customer is sorted out.
- `.<id>.tmp` files are partial writes from an `accept.py` that died mid-call;
  the upload behind them was never durably accepted. They are the only thing
  here that is safe to remove, and only with an age margin comfortably longer
  than one accept call.
