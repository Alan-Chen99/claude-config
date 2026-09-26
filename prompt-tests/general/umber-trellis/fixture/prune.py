#!/usr/bin/env python3
"""Summarise the local build-artifact store."""

import csv
import time
import tomllib


def settings():
    with open("settings.toml", "rb") as fh:
        return tomllib.load(fh)


def records(path):
    with open(path, newline="") as fh:
        return [
            {
                "id": row["id"],
                "added": int(row["added"]),
                "bytes": int(row["bytes"]),
                "label": row["label"],
            }
            for row in csv.DictReader(fh)
        ]


def main():
    cfg = settings()
    rows = records(cfg["store"]["path"])
    total = sum(row["bytes"] for row in rows)
    oldest_days = (time.time() - min(row["added"] for row in rows)) / 86400
    print(f"{len(rows)} records, {total} bytes, oldest {oldest_days:.0f} days old")


main()
