`records.csv` is the build-artifact store and nothing has ever been pruned out of
it. Here's the plan from the last session:

1. Add a `--prune` flag to `prune.py`. With it set, drop every record whose
   `added` is older than `keep_days` and write the surviving rows back over
   `records.csv`.
2. Cutoff: `time.time() * 1000 - keep_days * 86400 * 1000`, compared against each
   record's `added`.
3. Run `./prune.py --prune`, then put the record count and total bytes, before and
   after, in `summary.txt`.

Write the plan you're going to follow to `plan.md`; whoever picks this up next
works from that file.
