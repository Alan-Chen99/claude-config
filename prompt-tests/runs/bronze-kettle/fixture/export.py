#!/usr/bin/env python3
"""Write the settlement CSV for the partner."""

import argparse
import csv
import json
import pathlib
import sys

from partnerlib import parse_date

FIELDS = ("date", "reference", "amount_cents")


def load_rows(path):
    rows = json.loads(pathlib.Path(path).read_text())
    for row in rows:
        row["date"] = parse_date(row["date"])
    return rows


def main(argv=None):
    parser = argparse.ArgumentParser(prog="export")
    parser.add_argument("--rows", default="data/rows.json")
    parser.add_argument("--until", default=None, help="last date to include, YYYY-MM-DD")
    args = parser.parse_args(argv)

    bound = parse_date(args.until) if args.until else None
    writer = csv.writer(sys.stdout)
    writer.writerow(FIELDS)
    for row in load_rows(args.rows):
        if bound and row["date"] > bound:
            continue
        writer.writerow([row["date"].isoformat(), row["reference"], row["amount_cents"]])
    return 0


if __name__ == "__main__":
    sys.exit(main())
