The exporter can bound a settlement window at the top but not at the bottom, so
running a window means exporting from the beginning of time and trimming by hand.

Add `--since DATE` to `export.py`: the first date to include, inclusive, the mirror
of `--until`. The two should be usable together.
