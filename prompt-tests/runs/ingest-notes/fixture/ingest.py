#!/usr/bin/env python3
"""Load the day's CSV drops into the warehouse database."""
import os
import sqlite3
import sys
from pathlib import Path

import pandas as pd

MAX_RETRIES = 5
CHUNK_ROWS = 5000

TABLES = {
    "orders": "orders",
    "customers": "customers",
    "line_items": "line_items",
}


def connect(db_path):
    return sqlite3.connect(db_path, timeout=30.0)


def load_one(conn, csv_path, table):
    frame = pd.read_csv(csv_path, dtype=str)
    frame["source_file"] = csv_path.name
    for start in range(0, len(frame), CHUNK_ROWS):
        chunk = frame.iloc[start : start + CHUNK_ROWS]
        for attempt in range(MAX_RETRIES):
            try:
                chunk.to_sql(table, conn, if_exists="append", index=False)
                break
            except sqlite3.OperationalError:
                if attempt == MAX_RETRIES - 1:
                    raise
        conn.commit()


def main(drop_dir):
    conn = connect(os.environ["INGEST_DB"])
    for csv_path in sorted(Path(drop_dir).glob("*.csv")):
        table = TABLES.get(csv_path.stem)
        if table is None:
            print(f"skipping {csv_path.name}: no table for it", file=sys.stderr)
            continue
        load_one(conn, csv_path, table)
    conn.close()


if __name__ == "__main__":
    main(sys.argv[1])
