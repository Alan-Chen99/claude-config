# Decisions

Four constraints in this repo look arbitrary and are not. Each one below gives
the rule, the evidence behind it, how strong that evidence is, and what would
retire it. A rule stands until the thing that would retire it actually happens;
"it looks unnecessary" is not that thing.

---

## Thumbnail sharpness

**Rule.** `render.py` passes `resample` and `reducing_gap` explicitly. Keep it
that way. Pillow stays pinned in `requirements.txt`, and a bump ships only with
a look at real thumbnails before and after.

**Why.** February 2026: `requirements.txt` moved to `Pillow==10.3.0` and `md`
thumbnails came out visibly softer. Nobody noticed for a week; a customer
reported it. The bump was reverted, which is why the pin reads 10.2.0. The
diagnosis at the time was that 10.3 changed the resampling filter
`Image.thumbnail()` picks when the caller passes none, and `render.py` passed
none.

**Evidence.** The regression is real and customer-confirmed. The mechanism is
not: a later attempt to reproduce it failed.

- `Image.thumbnail`'s signature is `resample=Resampling.BICUBIC,
  reducing_gap=2.0` in both 10.2.0 and 10.3.0. Diffing `PIL/Image.py` between
  the two wheels shows the only changes to `thumbnail()` and `resize()` are
  type annotations and one refactored `if`/`else`; `reduce()` and `draft()` are
  identical.
- Running this repo's pipeline (`thumbnail()` then `save(quality=88)`) under
  both versions produced byte-identical resampled pixels and byte-identical
  JPEGs at all three sizes, across ten source classes: RGB PNG, RGB JPEG,
  grayscale, palette, CMYK, RGBA, EXIF-orientation-6, progressive/4:2:0, and a
  6000px source large enough to exercise the `reduce()` pre-step. The recorded
  digests in `test_invariants.py` are also identical under both versions.
  Method: `uv run --python 3.11 --with pillow==<version>`, manylinux x86_64
  wheels.
- The one behavioural difference found: a 16-bit grayscale PNG (`I;16`)
  thumbnails under 10.2.0 and raises `ValueError: image has wrong mode` under
  10.3.0. That is a crash, not a softening, and this pipeline cannot save such
  an image as JPEG under either version.

So something changed in that February deploy, and on the platform tested here
it was not the resampling behaviour of `Image.thumbnail` for any source class
listed above. What is left unchecked: production's actual source images, the
wheel or platform production runs, and whatever else shipped alongside the
bump. **Do not treat the softness as explained.** Treat the pin as protecting
against an unidentified cause, which is a stronger reason to keep it, not a
weaker one.

Passing the two arguments explicitly costs nothing today -- the values are
10.2.0's own defaults and output is byte-identical with and without them -- and
it removes one whole class of cause: sharpness is now a property of
`render.py`, not of whichever Pillow happens to be installed.

**What would retire the pin.** A Pillow bump that keeps `pytest -q`'s recorded
pixel digests green, plus one person looking at an `md` thumbnail of a real
photograph rendered before and after, is enough to unpin.

Both halves are needed, and the second is the load-bearing one. The digests are
identical under 10.2.0 and 10.3.0, so they would not have caught February; they
catch any future change to the resampling pipeline's output, which is a
different thing. A green suite is not permission to bump. If the digests do
move, the bump is a customer-visible change: look at the images, decide
deliberately, then re-record the digests and note why here.

---

## CDN purge batch size

**Rule.** `purge.CHUNK` stays at 50.

**Why.** March 2026: `purge.py` sent every URL in one call and started drawing
`429`s once batches passed a couple of hundred URLs. On a support call the
vendor's engineer said our plan caps a purge call at "around fifty" and that
the published limit of 500 applies to the enterprise plan. `CHUNK = 50`
stopped the `429`s.

**Evidence.** Weak in form, strong in effect. The number came from one verbal
statement, it appears nowhere in the vendor's documentation, and the docs
visibly contradict it. It has never been reproduced deliberately -- doing so
means provoking `429`s against production.

The trap for a future reader: the vendor's docs say 500, this file says 50, and
the docs look authoritative. They describe a plan we are not on.

**What would retire it.** Written confirmation from the vendor of the limit for
our specific plan, or a move to a plan whose documented limit we can rely on.
Either of those, not a reading of the public docs and not a quiet experiment in
production.

---

## Job files are the record of an accepted upload

**Rule.** Only `worker.py` removes files from `jobs/`. No cleanup script, no
retention policy, no disk-pressure sweep touches that directory. See
`jobs/README.md`, which is where someone writing such a script will look.

**Why.** April 2026: a cleanup script deleted `jobs/*.json` older than an hour
while the worker was mid-drain. Eleven customers had to be emailed and asked to
re-upload.

**Evidence.** Direct, and structural rather than incidental. `accept.py` writes
the file the moment an upload is accepted; `worker.py` removes it once the
thumbnails are out and `purge.py` has returned. Between those two points the
file is the only record that the upload was accepted at all. Deleting one loses
an upload with no error and no retry.

An old file is not a finished file. It means the worker has not reached it yet,
which points at the worker.

**Note on enforcement.** This is the one rule here that no test can hold.
`pytest -q` cannot see a `find -mtime +1 -delete` in an infra cron or a
host-level disk-pressure sweep, and the author of that script has no reason to
open this repo. Until the record moves out of the filesystem, the only real
protection is an explicit exclusion of this path in whatever owns retention on
the host, and someone has to put it there by hand.

**What would retire it.** A durable record of accepted uploads somewhere other
than this directory -- a database row, an append-only log -- that `worker.py`
marks complete. Until that exists, the file is the record.

---

## Logging, not `print()`

**Rule.** No `print()` anywhere in this repo. Use `logging`.

**Why.** Owner's preference, stated directly. `test_invariants.py` enforces it
so it does not have to be re-litigated in review.

**Note for whoever wires up the entry point.** `worker.py` logs through
`logging.getLogger(__name__)` and deliberately configures nothing. With no
handler installed, `log.info(...)` is discarded silently -- quieter than the
`print()` it replaced. Whatever calls `drain()` must call
`logging.basicConfig()` (or equivalent) at INFO or the per-job lines go
nowhere.

**What would retire it.** The owner saying so.
