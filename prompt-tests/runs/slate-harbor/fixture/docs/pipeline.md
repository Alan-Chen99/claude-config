# What writes into the archive

The collector (`ops/collector`, a separate service) rotates each producer's log
hourly and drops the rotated file into the shared archive directory. Several
producers write there:

| Producer | File names |
| --- | --- |
| our application | `app-YYYY-MM-DD.log` |
| the vendor bridge | `vendor-<host>.log` |
| the edge relay | `edge-<region>-<n>.log` |

The collector appends to a rotated file for a few minutes after creating it and
takes no lock, so a file's mtime moves after it first appears.
