# On-disk layout

A spool directory holds one file per artifact, plus `index.jsonl`.

`index.jsonl` carries one JSON object per line, one line per artifact:

    {"id": "a3f9c1", "recorded": "2026-09-01T10:04:00Z", "name": "build-2026-09-01.tar.gz"}

Every line in `index.jsonl` describes an artifact that is present on disk, so a
reader can count the lines to count the artifacts.

`prune` writes the surviving entries to `index.jsonl.tmp` and renames that over
`index.jsonl`, so the index file is never seen partially written.
