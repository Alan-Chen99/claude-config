# Restoring from a snapshot

The nightly job (`sync/uploader.py`, cron 02:15) writes one snapshot per table
to Tessera and appends it to `manifest.json`. `sync/restore.py` pulls the newest
entry back.

Run everything below from the repo root. `manifest.json` is opened as a relative
path, so `restore.py` dies with `FileNotFoundError` from anywhere else.

## Normal restore

```
python sync/restore.py /var/restore
```

It prints the key and the byte count it wrote. **That byte count is not a
check** — see the next section before you load anything.

## Verify before you load

`restore.py` does not compare what it downloaded against the manifest. It writes
whatever bytes arrive, prints the count, and exits 0. A truncated restore looks
exactly like a good one. The manifest already carries the size and sha256, so
check them by hand:

```
python3 - <<'EOF'
import json, hashlib, os, sys
entry = json.load(open("manifest.json"))["snapshots"][-1]
path = os.path.join("/var/restore", entry["key"])
size, sha = os.path.getsize(path), hashlib.sha256(open(path, "rb").read()).hexdigest()
print("key     ", entry["key"])
print("size     expected", entry["size"], "actual", size)
print("sha256   expected", entry["sha256"])
print("         actual  ", sha)
sys.exit(0 if size == entry["size"] and sha == entry["sha256"] else 1)
EOF
```

Exits non-zero on a mismatch. Do not `psql -f` a file that fails this.

## Known failure: the newest snapshot is short

This is the one you are most likely looking at. Roughly one restore in five has
come back truncated, always the newest snapshot.

**Why it happens.** `upload_snapshot` appends the manifest entry *before* it
uploads any bytes (`sync/uploader.py:67-69`), using the size and sha256 of the
local file. If a part upload then fails, `main` prints one line and moves on
(`sync/uploader.py:90-91`) — the manifest entry is not rolled back and the job
still exits 0, so cron reports success. The manifest is left advertising a
complete snapshot that is short or absent on Tessera.

**Why it is always the newest.** `newest()` returns `snapshots[-1]`
(`sync/restore.py:16`) and there is no way to ask for anything else. A failed
upload appends its entry last, so the broken entry is exactly the one
`restore.py` picks. This does *not* mean older snapshots are good — it means
`restore.py` has never fetched one.

**Telling the two truncation modes apart.** Download twice and compare sizes:

- Same short size both times — the object on Tessera is short. The upload never
  completed. Re-downloading will not help; use an older snapshot.
- Different sizes — the transfer is dropping mid-stream. `restore.py` reads with
  a size argument (`sync/restore.py:26`), and CPython's `http.client` chooses not
  to raise `IncompleteRead` on that path, so a dropped connection ends the loop
  silently. Retrying may get you a complete file, but verify it every time.

## Restoring an older snapshot

`restore.py` cannot do this. Pick the entry you want from `manifest.json` and
fetch it yourself:

```
KEY=orders-2026-09-17.dump
curl -fSL --retry 3 -o "/var/restore/$KEY" "$TESSERA_ENDPOINT/$TESSERA_BUCKET/$KEY"
sha256sum "/var/restore/$KEY"     # compare against the manifest entry by hand
```

`curl -f` fails loudly on a 404, which is what you get if that upload never
completed either. Work backwards until one verifies.

## If the manifest and the object disagree

Tessera is strongly consistent, but the guarantee is scoped to *once an upload
returns*: after that the key is readable and every reader sees the same bytes.
The uploader publishes the manifest entry before the upload returns, so a
manifest entry is not evidence that the object is complete. A mismatch is
usually a failed or unfinished upload, not a reader-side problem and not
replication lag.

Check the 02:15 cron output for the run that produced the entry. An
`upload failed for <key>: ...` line there confirms it; absence of one does not
rule it out, since only `URLError` and `HTTPError` are caught and reported.

## Escalation

Page the data platform on-call rota.

Re-running the nightly job by hand is **not** free: `main()` re-uploads every
file still in `snapshots/` and appends a fresh manifest entry for each, so a
file that lingers gets duplicate entries, and the newest one wins on the next
restore. Check what is in `snapshots/` first.

The underlying bug in `sync/uploader.py` is not fixed. Until it is, treat the
verification step above as mandatory on every restore.
