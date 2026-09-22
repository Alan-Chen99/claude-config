"""Pull the newest snapshot back down from Tessera."""

import json
import os
import sys
import urllib.request

from uploader import BUCKET, ENDPOINT, MANIFEST


def newest():
    with open(MANIFEST) as fh:
        snapshots = json.load(fh)["snapshots"]
    if not snapshots:
        sys.exit("manifest is empty")
    return snapshots[-1]


def restore(dest_dir):
    entry = newest()
    url = f"{ENDPOINT}/{BUCKET}/{entry['key']}"
    dest = os.path.join(dest_dir, entry["key"])
    with urllib.request.urlopen(url, timeout=120) as resp, open(dest, "wb") as out:
        while True:
            chunk = resp.read(1 << 20)
            if not chunk:
                break
            out.write(chunk)
    print(f"restored {entry['key']} ({os.path.getsize(dest)} bytes)")
    return dest


if __name__ == "__main__":
    restore(sys.argv[1] if len(sys.argv) > 1 else ".")
