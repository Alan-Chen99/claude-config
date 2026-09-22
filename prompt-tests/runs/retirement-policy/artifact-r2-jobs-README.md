# Do not delete anything in this directory by age

`jobs/<id>.json` is written by `accept.py` the moment an upload is accepted and
removed by `worker.py` once the thumbnails are rendered and the CDN purge has
returned. Between those two moments the file is the **only** record that the
upload was accepted; nothing else in this system records one. Deleting a job
file loses a customer's upload silently, and the customer finds out, not us.

In April a cleanup script deleted `*.json` here older than an hour while the
worker was mid-drain. Eleven customers were emailed and asked to re-upload.

Rules:

- **`worker.py` is the only thing that removes `jobs/*.json`.** Not cron, not a
  disk-pressure script, not a deploy step.
- **Age is not staleness.** `worker.py` leaves a job file in place whenever
  rendering or purging raises, so a job can sit here through an outage and
  still be owed. An hour, a day and a week are all normal.
- A backlog here is a stuck worker. Fix the worker; the files are the work.

`jobs/.<id>.tmp` is the exception. `accept.py` writes one and renames it into
place, and only the rename makes an upload accepted, so a leftover `.tmp` is an
upload the caller was never given an id for. Those are safe to remove.
