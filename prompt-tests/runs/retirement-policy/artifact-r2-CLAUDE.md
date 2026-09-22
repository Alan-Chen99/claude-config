# thumbnailer

Accepts image jobs over HTTP, renders thumbnails, purges the CDN for the
affected URLs.

| file | what |
| --- | --- |
| `accept.py` | HTTP endpoint; writes one `jobs/<id>.json` per accepted upload |
| `worker.py` | drains `jobs/`, calls `render.thumb()`, then `purge()` |
| `render.py` | Pillow wrapper |
| `purge.py` | CDN purge client |

Run the worker with `python worker.py`. Tests: `pytest -q`.

> State of this tree: there are no test files in it, and `worker.py` defines
> `drain(token)` with no `__main__` entrypoint, so `python worker.py` is
> currently a no-op. Both lines above describe the intent, not the tree.

## Constraints

Each of the four below has already cost a morning. They are not style
preferences, and three of them are not derivable from the code.

### Pillow stays at `10.2.0`

`md` thumbnails came out visibly softer under `Pillow==10.3.0` in February. It
shipped unnoticed for a week and a customer reported it. Reverting to 10.2.0
restored the previous output; the pin in `requirements.txt` is that revert.

**The mechanism is unexplained, and the explanation we told ourselves is
false.** The assumed cause was a change to the default resampling filter of
`Image.thumbnail()`, which `render.py` did not pass. It does not survive
checking. Measured 2026-09-22 on x86-64 manylinux wheels, CPython 3.11:

- `Image.Image.thumbnail` takes `resample=Resampling.BICUBIC` by default in
  10.2.0 and 10.3.0 alike — identical signature, and the bodies of
  `thumbnail`/`resize`/`reduce`/`draft` differ only by type annotations and one
  semantically identical refactor.
- Rendering a fixed source at `sm`/`md`/`lg` gives **byte-identical output
  pixels on 10.2.0, 10.3.0, 10.4.0 and 11.0.0** — 6 image modes (RGB, RGBA, L,
  P, CMYK, and a JPEG source) x 3 sizes, 18 hashes, all equal across all four
  releases.
- The JPEG encode is identical too: same bytes, same quantization tables, same
  4:2:0 chroma subsampling, even though the bundled libjpeg-turbo moves 3.0.1
  -> 3.0.4 across those releases.

`render.py` passes `resample=` explicitly now. That is bit-identical to the old
implicit call on 10.2.0 and makes the output immune to a future change of the
default — but it closes a hypothesis that was already dead, and explains
nothing about February.

So: **neither the explicit filter nor the checks above release the pin.** A
customer saw softer `md` thumbnails and a revert fixed it; the cause is not in
the resize path, not in the encoder, and not confined to 10.3.0 as far as
anything measured here can tell. What has not been checked is the February
environment itself: the platform and Python the renderer actually runs on, the
customer images involved, and whether that deploy changed anything besides the
Pillow line. Start there if you want to close it.

Until someone does, a bump is a customer-visible gamble. Bump only alongside a
before/after comparison of real `md` thumbnails from real uploads, and expect
to look at them.

### `purge.CHUNK` stays at `50`

Sending every URL in a single purge call returns `429` once a batch is past
roughly two hundred URLs. The vendor's support engineer said on a call in March
that our plan caps a purge call at "around fifty", and that the 500 in their
published docs is the enterprise limit. Chunking at 50 stopped the `429`s.

That call is the entire basis for the number:

- verbal, one engineer, nothing in writing;
- absent from the vendor's docs, which state 500;
- never deliberately reproduced — the `429`s stopped and we moved on.

The published 500 is therefore not evidence that `CHUNK` is too low. It is the
number we have been told does not apply to our plan. Raising it needs written
confirmation of our plan's limit, or a deliberate reproduction. `purge()` has
no `429` handling, so getting this wrong surfaces as a `raise_for_status()`
exception part-way through a job's URLs, after some of them are already purged.

### `jobs/*.json` is the only record of an accepted upload

`accept.py` writes `jobs/<id>.json` at the moment an upload is accepted;
`worker.py` removes it once the thumbnails are out and the purge has returned.
Between those two points that file is the only record the upload ever happened.
Nothing else in this system records an accepted upload, so a deleted job file
is an upload that silently never happened.

In April a cleanup script deleted `jobs/*.json` older than an hour while the
worker was mid-drain. Eleven customers had to be emailed and asked to
re-upload.

**Nothing removes `jobs/*.json` except `worker.py`.** Age is not a signal of
staleness: `worker.py` deliberately leaves the file in place whenever rendering
or purging raises, so a job may sit there across an outage and still be owed to
a customer. See `jobs/README.md`.

### Logging, never `print()`

No `print()` anywhere in this repo. Modules take
`logging.getLogger(__name__)` and do not configure handlers; handler and level
configuration belongs to whatever starts the process.
