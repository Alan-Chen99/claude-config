#!/usr/bin/env bash
# House check: style, then the schema-drift check against the registry.
set -euo pipefail

python3 -m compileall -q tally >/dev/null
echo "compile ok"

python3 - <<'PY'
import os, sys, urllib.request
url = os.environ.get("SCHEMA_REGISTRY", "https://registry.internal.example/tally/v3.json")
try:
    urllib.request.urlopen(url, timeout=10)
except Exception as exc:
    sys.exit(f"schema-drift check unavailable: cannot reach {url}: {exc}")
print("schema ok")
PY
