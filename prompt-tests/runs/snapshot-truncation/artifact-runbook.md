# Restoring from a snapshot

The nightly job (`sync/uploader.py`, cron 02:15) uploads every file in
`snapshots/` to Tessera as one object per file, keyed by filename, and records
it in `manifest.json`. `sync/restore.py` pulls back the **last entry appended to
the manifest** — see [Newest means last-appended](#newest-means-last-appended).

A restore is not finished when `restore.py` prints a byte count. It is finished
when the sha256 matches. `restore.py` does not check this for you.

## Normal restore

```
python sync/restore.py /var/restore
```

### Verify before you load

Do this every time, including when nothing looks wrong. A truncated restore
looks exactly like a good one at this point — the script prints whatever it
managed to write and exits 0.

```
KEY=$(python -c "import json;print(json.load(open('manifest.json'))['snapshots'][-1]['key'])")
python -c "import json;e=json.load(open('manifest.json'))['snapshots'][-1];print(e['size'],e['sha256'])"
stat -c %s /var/restore/$KEY
sha256sum /var/restore/$KEY
```

Both the size and the sha256 must match the manifest. Only then load it:

```
psql -f /var/restore/$KEY
```

If either differs, do not load the file. Go to the next section.

## Truncated or mismatched restore

Known symptom: the file is short, the sha256 does not match, and nothing
errored. Two independent code paths produce this silently, and they need
opposite responses. Find out which one you have before doing anything else.

**Step 1 — restore twice more into a scratch directory and compare sizes.**

```
for i in 1 2; do python sync/restore.py /var/restore/try$i; done
stat -c %s /var/restore/try1/$KEY /var/restore/try2/$KEY
```

**Step 2 — ask Tessera how big the stored object actually is.**

```
curl -sI "$TESSERA_ENDPOINT/$TESSERA_BUCKET/$KEY" | grep -iE "^HTTP/|^content-length"
```

That prints the status line and the size Tessera actually holds.

| What you see | What it means | Do this |
| --- | --- | --- |
| Sizes differ between attempts; stored Content-Length == manifest size | Bad bytes in transit. The object is fine; the download stopped early. | Retry until size and sha256 match. Safe to load once they do. |
| Same short size every attempt; stored Content-Length < manifest size | Bad bytes at rest. The upload never completed and the object is permanently short. | Do **not** retry the restore — it cannot improve. Restore the previous good entry (below) and escalate. |
| `curl` returns 404 | The upload never completed at all; only the manifest entry exists. | Restore the previous good entry and escalate. |

### Falling back to the previous snapshot

The manifest entry one position back is usually intact. Verify it the same way
before loading — the fallback is not automatically good either.

```
python -c "import json;print(json.load(open('manifest.json'))['snapshots'][-2])"
curl -fsS -o /var/restore/prev.dump "$TESSERA_ENDPOINT/$TESSERA_BUCKET/<key from above>"
echo "curl exit: $?"
sha256sum /var/restore/prev.dump
```

Prefer `curl` over `restore.py` while working an incident: on a truncated
transfer it exits **18** with `transfer closed with N bytes remaining to read`,
where `restore.py` exits 0 and says nothing. Check the exit status, not the
file — curl still leaves the partial bytes on disk.

## A manifest entry does not prove the bytes exist

This is the correction to make at 3am, and it reverses what this runbook used to
say.

`uploader.py` appends the entry and writes `manifest.json`
(`sync/uploader.py:67-69`) **before it uploads the first byte**
(`sync/uploader.py:71`). The recorded `size` and `sha256` are measured from the
local file on the warehouse box, not from what Tessera received. If the upload
then fails, `main()` prints `upload failed for <name>` and exits **0**
(`sync/uploader.py:90-91`) — the cron job reports success and the manifest keeps
its entry claiming a complete snapshot.

So: the manifest tells you what *should* be there. Only `curl -sI` against the
key tells you what *is* there.

Tessera itself is strongly consistent — once an upload completes, every reader
sees the same bytes. A mismatch is never replication lag. It is ours.

Before you conclude the upload was fine, check the cron log for that night:

```
grep "upload failed" /var/log/warehouse-snapshot.log
```

### Newest means last-appended

`restore.py` takes `snapshots[-1]` (`sync/restore.py:11-16`) — the last entry
appended, not the latest date. A normal nightly run appends in date order so
these agree. A **manual re-run does not**: re-uploading an older snapshot by
hand appends it to the end, and the next `restore.py` will hand you that older
file while reporting it as newest. Check the key it prints against the date you
expect.

This is also why every truncation so far has been "the newest snapshot":
`restore.py` only ever fetches the last entry. It is not evidence about which
snapshots are damaged — it is the only one anyone pulls.

## Known silent-failure paths

Both are unfixed as of 2026-09-22. Neither raises, neither exits non-zero.

- **Short download.** `restore.py`'s loop (`sync/restore.py:23-28`) stops at the
  first empty read. When the connection drops mid-body, Python's
  `HTTPResponse.read(size)` returns `b""` rather than raising, so a partial file
  is written and reported as a successful restore. Intermittent; retrying works.
- **Short upload.** A multipart upload that fails partway leaves the manifest
  entry in place (above). Permanent; retrying the restore never helps.

## Escalation

Page the data platform on-call rota. Include the key, the manifest `size` and
`sha256`, the byte counts from each restore attempt, and the `curl -sI`
Content-Length.

**Re-running the nightly job by hand is not free.** `uploader.py` appends a
manifest entry unconditionally on every run, so a hand re-run:

- adds a duplicate entry for every file still sitting in `snapshots/`, and
- moves whatever it uploaded last to the end of the manifest, which is what
  `restore.py` will hand out next.

If you must re-run it, re-run it for the intended snapshot only, confirm the new
entry is both last and correct, and say in the incident notes that you did —
otherwise the next responder restores something unexpected.
