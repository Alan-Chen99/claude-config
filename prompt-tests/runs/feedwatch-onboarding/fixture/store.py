"""SQLite row store for feed entries."""

import sqlite3

DB = "feedwatch.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS entries (
    id      TEXT,
    title   TEXT,
    updated TEXT
)
"""


def _conn():
    c = sqlite3.connect(DB)
    c.execute(SCHEMA)
    return c


def put(entry_id, title, updated):
    c = _conn()
    c.execute(
        "INSERT INTO entries (id, title, updated) VALUES (?, ?, ?)",
        (entry_id, title, updated),
    )
    c.commit()
    c.close()


def count():
    c = _conn()
    n = c.execute("SELECT count(*) FROM entries").fetchone()[0]
    c.close()
    return n
