Two changes to the spool.

1. `spool prune` should take `--older-than <duration>` in place of `--days N`,
   accepting `90m`, `36h` and `30d`, and drop artifacts recorded longer ago
   than that.
2. Pruning rewrites the whole index today. Change it so a prune appends a
   removal record to `index.jsonl` rather than rewriting the file, so the cost
   of a prune follows what it removes and not the size of the spool.

Keep the tests passing.
