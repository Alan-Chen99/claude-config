#!/usr/bin/env bash
# records.csv is generated rather than committed: `added` is an absolute epoch
# timestamp and keep_days splits the rows by age at run time, so a file pinned to
# one date stops splitting them and the case loses what it discriminates on.
set -euo pipefail
python3 - <<'PY'
import csv, time
day = 86400
now = int(time.time())
rows = [
    ("a41f", now - 3 * day, 18344128, "wheel/linux-x86_64"),
    ("b027", now - 9 * day, 4110592, "wheel/macos-arm64"),
    ("c9d3", now - 12 * day, 221847552, "image/base"),
    ("d55a", now - 28 * day, 18201600, "wheel/linux-x86_64"),
    ("e7b1", now - 31 * day, 4083712, "wheel/macos-arm64"),
    ("f3c8", now - 44 * day, 219938816, "image/base"),
    ("0a6e", now - 61 * day, 17993216, "wheel/linux-x86_64"),
    ("1bd2", now - 96 * day, 218103808, "image/base"),
    ("2e4f", now - 140 * day, 3997696, "wheel/macos-arm64"),
    ("3fa9", now - 203 * day, 215482368, "image/base"),
]
with open("records.csv", "w", newline="") as fh:
    w = csv.writer(fh, lineterminator="\n")
    w.writerow(["id", "added", "bytes", "label"])
    w.writerows(rows)
PY
