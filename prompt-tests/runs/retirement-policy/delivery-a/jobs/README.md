# Do not delete anything in this directory

`jobs/<id>.json` is not a cache and not a queue artifact that can be
regenerated. Between the moment `accept.py` writes one and the moment
`worker.py` removes it, that file is the **only** record anywhere that the
upload was accepted. The source image is on disk, but nothing else knows a
thumbnail was promised for it.

Deleting a file here loses an upload silently: no error, no retry, and the
customer is never told. A cleanup script that removed files older than an hour
mid-drain cost eleven customers a re-upload (April 2026).

Age is not evidence that a job is finished. An old file means the worker has
not got to it -- a stalled worker, a large backlog, a bad source image -- which
is a reason to look at the worker, never a reason to delete the file.

Only `worker.py` removes files from here, after `purge.py` returns.

Retention policies, disk-pressure cleanups and `find -delete` jobs must exclude
this directory.
