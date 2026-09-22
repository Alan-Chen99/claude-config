# Restoring from a snapshot

The nightly job (`sync/uploader.py`, cron 02:15) writes one snapshot per table
to Tessera and appends it to `manifest.json`. `sync/restore.py` pulls the newest
entry back.

## Normal restore

```
python sync/restore.py /var/restore
```

It prints the key and the byte count it wrote. Load that file with the usual
`psql -f`.

## If the restore looks wrong

Check `manifest.json` first — the entry carries the key, the size and the
sha256 as they were on the warehouse box.

Tessera is strongly consistent: once an upload returns, the key is readable and
every reader sees the same bytes. So a mismatch between the manifest and what
came down is a problem on our side, not a replication lag.

## Escalation

Page the data platform on-call rota. Snapshot keys are never reused, so it is
always safe to re-run the nightly job by hand.
