# spool

`bin/spool` reports the state of the jobs in `queue.jsonl`.

```
bin/spool [--file PATH] [--state NAME]
```

## Flags

| Flag           | What                                                 |
| -------------- | ---------------------------------------------------- |
| `--file PATH`  | read this queue file instead of `queue.jsonl`        |
| `--state NAME` | report only jobs whose state is `NAME`               |
| `--help`       | print the usage message                              |

One tab-separated line per reported job — id, state, attempts — then a summary
line counting what was reported and how many jobs have failed. Exit status is 1
when any job in the file has failed, whatever the filter reports, and 0
otherwise.
