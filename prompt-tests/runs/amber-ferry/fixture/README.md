# spool

`spool` stores build artifacts under a spool directory and keeps an index of
them, so that old ones can be dropped without walking the directory.

## Example

    $ spool add build-2026-09-01.tar.gz
    added a3f9c1
    $ spool list
    a3f9c1  2026-09-01T10:04:00Z  build-2026-09-01.tar.gz
    $ spool prune --days 7
    pruned 3

Pruning rewrites the index in full, so an interrupted prune leaves the index on
disk either wholly old or wholly new.
