"""Regenerate tally/_generated/schema.py from the schema registry."""

import os
import sys
import urllib.request

REGISTRY = os.environ.get("SCHEMA_REGISTRY", "https://registry.internal.example/tally/v3.json")

if __name__ == "__main__":
    try:
        with urllib.request.urlopen(REGISTRY, timeout=10) as response:
            payload = response.read()
    except Exception as exc:
        sys.exit(f"cannot reach schema registry at {REGISTRY}: {exc}")
    print(payload)
