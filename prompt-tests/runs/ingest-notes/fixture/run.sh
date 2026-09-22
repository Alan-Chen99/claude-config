#!/usr/bin/env bash
set -euo pipefail
: "${INGEST_DB:?set INGEST_DB to the warehouse database path}"
DROP_DIR="${1:-./drops}"
python3 -c "import sqlite3,sys; sqlite3.connect(sys.argv[1]).executescript(open('schema.sql').read())" "$INGEST_DB"
exec python3 ingest.py "$DROP_DIR"
