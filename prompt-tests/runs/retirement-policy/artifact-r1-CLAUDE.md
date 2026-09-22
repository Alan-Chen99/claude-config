# thumbnailer

Accepts image jobs over HTTP, renders thumbnails, purges the CDN for the
affected URLs.

| file | what |
| --- | --- |
| `accept.py` | HTTP endpoint; writes one `jobs/<id>.json` per accepted upload |
| `worker.py` | drains `jobs/`, calls `render.thumb()`, then `purge()` |
| `render.py` | Pillow wrapper |
| `purge.py` | CDN purge client |
| `test_guards.py` | one test per invariant below |

Tests: `pytest -q`, with `requirements.txt` installed.

`worker.py` defines `drain(token)` and has no `__main__` block, so
`python worker.py` runs nothing. Whichever process calls `drain()` owns
`logging` setup: modules here log through `logging.getLogger(__name__)` and
install no handler, so an unconfigured entrypoint discards every line.

## Invariants

Four failures cost a morning each. Three are invisible in the code, and one of
those is contradicted by the vendor's own documentation, so a reader who
reasons from the code and the docs alone will reintroduce it. Each has a test
in `test_guards.py`; the reasoning lives next to the code it constrains.

### `jobs/<id>.json` is the only record that an upload was accepted

`accept.py` creates it the moment an upload is accepted. `worker.py` removes it
after the thumbnails render and the purge returns. Between those two moments
nothing else knows the upload exists — no database row, no log line, no queue.

**Only `worker.py` removes a file from `jobs/`.** No age-based cleanup, no
`find -mtime`, no tmpreaper, no cron sweeper, no "clear stale jobs" deploy
step. A sweeper deleting `jobs/*.json` older than an hour mid-drain destroyed
the only evidence of eleven accepted uploads. Nothing could enumerate what had
been lost, so all eleven customers were emailed and asked to upload again.

Stops applying once an accepted upload is durably recorded somewhere else.

### `CHUNK = 50` in `purge.py` contradicts the published limit on purpose

The documented 500 is the enterprise plan's; ours is lower. The whole basis for
50 — including how thin it is, and what would justify moving it — is in the
comment at the constant, which is the only place that knowledge exists.

### Thumbnail output must never come from a Pillow default

`render.py` names its resample filter rather than inheriting one. The pin and
its real justification are in `requirements.txt`, and that justification is not
the one usually given: February's softness was blamed on a changed Pillow
default, and testing does not support that. Read the note before bumping.

### Logging, never `print()`

No `print()` anywhere in this repo.

## Known gaps

Not incidents, but each one costs time on first contact:

- `out/` is not created by anything; `render.thumb()` fails if it is absent.
- `render.thumb()` always encodes JPEG, so an RGBA source (`accept.py` takes
  `.png` uploads) raises on save.
- `worker.py` leaves the job file handle open (`json.load(open(path))`).
- There is no HTTP server here; `accept.py` is only the accept function.
