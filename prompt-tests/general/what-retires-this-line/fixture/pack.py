#!/usr/bin/env python3
"""Group queued row files into one payload file per call; print its path."""
import json, sys, tempfile

rows = [json.load(open(p)) for p in sys.argv[1:]]
with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as fh:
    json.dump({"rows": rows}, fh)
    print(fh.name)
