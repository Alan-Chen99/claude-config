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
