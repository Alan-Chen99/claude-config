# Brief: truncated restores from `warehouse-snapshots`

You have this repo and nothing else. This brief is the whole handoff. Read it,
then verify its claims against the code yourself before you change anything —
sections are marked with how much they can be trusted.

## 1. The report (unverified — secondhand, no logs available)

Restores came back **truncated** three times in the week ending 2026-09-22.
Roughly **one in five** attempts. Every time it was **the newest snapshot**.

That is the entire observed evidence. Nobody captured a byte count, a manifest
entry, a failing key, or a cron log, and this repo contains none. Treat the
three properties above as the constraints any theory must satisfy; treat
nothing else about the incidents as known.

## 2. What the repo is

Nightly `pg_dump` output lands in `snapshots/`. `sync/uploader.py` runs from
cron at 02:15, uploads each file to Tessera object storage via multipart, and
appends an entry (`key`, `sha256`, `size`) to `manifest.json`.
`sync/restore.py` reads the manifest, takes one entry, and downloads it.
`docs/restore.md` is the on-call runbook.

`snapshots/orders-2026-09-18.dump` in this repo is a 75-byte placeholder, not a
real dump. You cannot reproduce anything by running the job as-is against real
data; build a fake endpoint or a unit-level harness instead.

## 3. Verified defects

Facts about the source, not inferences about the incidents. D1-D6 are read
straight off the code and are cheap to re-confirm; D7 I confirmed by running
it.

**D1 — The manifest is committed before a single byte is uploaded.**
`uploader.py:67-69` reads, appends and writes the manifest. The upload does not
start until `:71` and does not finish until `:82`. So the manifest asserts a
key, a size and a sha256 that may never become true.

**D2 — Upload failures are swallowed.** `uploader.py:88-91` catches
`URLError`/`HTTPError`, prints a line, and continues the loop. `main()` returns
normally and the cron job exits 0. Combined with D1, a failed upload leaves a
manifest entry pointing at an object that is absent or partial, and nothing
alerts.

**D3 — Nothing ever verifies bytes against the recorded digest.** The uploader
never re-reads what it wrote. `restore.py` downloads (`:23-28`) and prints the
byte count (`:29`) but never compares it to `entry["size"]`, and never hashes
the result against `entry["sha256"]`. The digest is recorded and then never
used by any code path in the repo. This is the defect that makes truncation
*silent*: whatever length comes down is accepted and handed to `psql -f`.

**D4 — `sha256` and `size` are measured from different reads than the upload.**
`uploader.py:65` reads the whole file to hash it; `:68` calls `getsize()`;
`:73-80` opens the file again and uploads whatever is there at that moment.
Three separate observations of a growing file, with no lock and no completion
signal, in that order. If the file grows between them then
`hash_bytes <= manifest_size <= uploaded_bytes`, so the manifest records a size
that is too small *and* a digest that covers even fewer bytes than that — the
recorded digest does not describe the recorded size, let alone the object that
was actually stored.

**D5 — "Newest" is positional, not chronological.** `restore.py:16` returns
`snapshots[-1]` — the last line in the file. `uploader.py:87` uploads every
entry in `snapshots/` on every run and D1 appends unconditionally, so a
re-upload of an old dump appends a duplicate entry and becomes "newest".
`docs/restore.md:27-28` tells on-call that re-running the job by hand is
*always safe*, which walks straight into this.

**D6 — Responses are not checked.** `_put_part` (`:35-42`) discards the status
it was handed. `_complete_multipart` (`:45-47`) discards the response entirely,
so an error returned in a 200 body — normal for complete-multipart in
S3-compatible stores — reads as success. `_complete_multipart` also sends a
bare etag list with the part numbers stripped (`:46`), discarding the ordering
information the code already had.

**D7 — The download loop exits silently on a body that is cut short.**
`restore.py:23-28` loops on `resp.read(1 << 20)` and breaks on the first empty
return. I tested this against a local server: when a response declares
`Content-Length: 1000` and then sends 300 bytes and closes, **the loop exits
cleanly with 300 bytes written and no exception raised** — `urllib` does not
compare what it read to the declared length on this path. (A *chunked* response
cut short does raise `IncompleteRead`; a `Content-Length` one does not.) So any
connection dropped mid-download produces a short file that `restore.py:29`
reports as a normal success.

## 4. Lead hypothesis (inference — not confirmed, confirm or kill it first)

**The uploader uploads dumps that `pg_dump` has not finished writing.**

Cron fires at a fixed 02:15. Nothing in `main()` checks that a file is complete
— no sentinel, no rename-on-close, no size-stable check, no lock. At `:73-80`
the read loop stops at whatever EOF exists at that instant, `:82` completes the
multipart normally, and the object in Tessera is genuinely short. D3 then means
the restore never notices.

It is the lead because it is the only mechanism I found that produces all three
reported properties at once: truncation rather than an error (the upload
*succeeds*, it is just short); always the newest snapshot (only the one being
written that night can be incomplete); intermittently (it depends on whether
the dump finished before 02:15 — a dump whose runtime is creeping toward the
cron time would drift into failing some nights and not others).

**Confirm it before fixing it**, and note the two candidates leave opposite
fingerprints — this is the cheapest discriminator available. For an affected
key, get three numbers: the object's real size in Tessera, its `size` in
`manifest.json`, and the final size of that dump on the warehouse box.

- **This hypothesis:** `manifest_size < tessera_size < dump_size`, and the
  manifest `sha256` matches *neither* the object nor the dump. The manifest's
  size and digest were taken at `:68` and `:65`, before the upload read at
  `:73-80` picked up more bytes (see D4), so the manifest undershoots the
  object rather than overshooting it. Get this direction right — it is the
  whole test.
- **D7 instead:** `manifest_size == tessera_size == dump_size` and the manifest
  `sha256` matches the stored object cleanly; only the file that landed in
  `/var/restore` was short. Then the upload side is fine and the loss is in
  transit.

If neither pattern holds, both theories are wrong. Say so and re-derive rather
than fitting the nearest one.

D7 ranks second only because it does not explain *always the newest snapshot*
on its own — nothing makes the newest key likelier to drop mid-transfer. On
every other count it fits as well as the lead does, and unlike the lead it is
confirmed behavior rather than inference.

**Other alternatives I could not rule out:**
- A partial multipart that the store completes anyway, or a complete-multipart
  error returned in a 200 body (D6).
- Something outside this repo entirely — the dump job, the cron wrapper, the
  Tessera side. The repo cannot see any of it.

D3 is the root enabler under every one of these, D7 included — and under the
ones I have not thought of. Fix it whether or not the lead hypothesis survives.

## 5. Also wrong in `docs/restore.md`

`docs/restore.md:21-23` says a manifest/bytes mismatch cannot be replication
lag because Tessera is strongly consistent. Given D1, that reasoning is broken:
the manifest is written *before* the upload, so a mismatch is fully expected
during and after a failed run and says nothing about the store. The runbook
sends on-call looking in the wrong direction. Fix the doc as part of the change
— including the "always safe to re-run" claim in `:27-28`, which is false while
D5 stands.

## 6. Scope and acceptance

Fix the defects, not just the symptom. Minimum bar:

1. A restore that does not match the manifest's `sha256` **and** `size` fails
   loudly and non-zero, and does not leave the bad file where `psql -f` would
   find it.
2. A manifest entry exists only for an object that is fully uploaded and
   verified. Order the writes accordingly.
3. An upload failure makes the cron job exit non-zero. Per-file outcomes are
   reported individually; a partial batch is not a success.
4. The uploader refuses to upload a file it cannot establish is complete, and
   the size and digest it records come from the same bytes it actually sent.
5. `restore.py` selects the intended snapshot explicitly rather than by list
   position, and duplicate keys cannot silently accumulate in the manifest.
6. `docs/restore.md` matches the new behavior, §5 included.

Tests: integration-level against a fake Tessera endpoint (a local HTTP server
is enough). Cover at least — upload interrupted mid-part; a short file that
uploads "successfully"; a download cut short; a manifest whose digest does not
match the bytes. Each must fail loudly. Do not test by mutating the placeholder
dump into something that looks real; generate fixtures.

**Do not** add a retry, a fallback, or a "best effort" path that lets a restore
proceed on unverified bytes. A restore that stops is recoverable; one that
loads a truncated dump into the warehouse is not.

## 7. What I did not do

No git history (this is not a git repo), no logs, no access to the warehouse
box or to Tessera, and no run of either script against a real endpoint. The one
thing I did execute is the D7 probe: a local socket server returning a short
body, driven through the same read loop `restore.py` uses.

Every claim in §3 comes from reading the two files, except D7 which I confirmed
by experiment. Everything in §4 is inference from those readings plus the three
reported symptoms. If the symptoms turn out to contradict §4, trust the
symptoms.
