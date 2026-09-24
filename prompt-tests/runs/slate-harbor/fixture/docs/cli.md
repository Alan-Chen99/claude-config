# prune

```
prune.py [--config PATH] [--archive DIR]
```

| Flag | Default | What |
| --- | --- | --- |
| `--config` | `logkeep.conf` | settings file |
| `--archive` | from the settings file | directory to prune |

## Settings

`logkeep.conf`, section `[logkeep]`:

| Setting | Example | What |
| --- | --- | --- |
| `archive` | `archive` | directory holding the log files |
| `retain` | `14d` | keep files younger than this; `h`, `d` and `w` suffixes |

Every file matching `*.log` in the archive directory is a candidate. A file older
than `retain` is deleted; the path of each deletion is printed.
