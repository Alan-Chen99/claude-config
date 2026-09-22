# thumbd

Renders thumbnails for uploaded images and pushes them to the CDN bucket.

## Layout

| Path | What |
| --- | --- |
| `render.py` | Renders one upload id and uploads the result. One process per job. |
| `worker.py` | Pulls job ids off the queue and runs `render.py` for each. |
| `cache/` | Decoded source images, written by the upload handler, one file per id. |

## Running it

`CDN_TOKEN` comes from the ops vault. Rendering is idempotent — the same upload
id overwrites the same object.
