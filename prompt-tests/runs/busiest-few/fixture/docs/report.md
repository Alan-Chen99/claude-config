# `tally report`

```
python3 -m tally report LOGFILE [--since YYYY-MM-DD]
```

Prints one line per source, `<count>\t<source>`, most frequent first.

- `LOGFILE` — path to a tab-separated log file.
- `--since YYYY-MM-DD` — count only records on or after this date.
