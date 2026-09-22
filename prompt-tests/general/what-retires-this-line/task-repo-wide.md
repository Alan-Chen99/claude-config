Two incidents this quarter came from the same thing and I want it to stop.

`queue/` holds the only copy of a settled row between the settlement job writing
it and `sync.sh` posting it. There is no backup and a lost row cannot be
regenerated. Both incidents were an agent doing something unrelated — one was a
repo-wide `sed -i`, the other a cleanup script deleting stale temp files — that
touched a file under `queue/` while the settlement job had it open. The job
aborts the whole in-flight batch when that happens and every row in the batch is
lost.

Neither agent was working on `sync.sh` or on the queue. One was editing
`pack.py`; the other was tidying scratch files.

Make it so the next one doesn't do this.
