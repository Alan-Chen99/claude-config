#!/usr/bin/env python3
"""Render one upload id into a thumbnail and push it to the CDN bucket."""
import os
import sys
import time
import urllib.request
from pathlib import Path

CACHE = Path("cache")
BUCKET = "https://cdn.example/thumbs"
EDGE = 256


def source_bytes(upload_id: str) -> bytes:
    return (CACHE / f"{upload_id}.raw").read_bytes()


def thumbnail(blob: bytes) -> bytes:
    from PIL import Image
    import io

    img = Image.open(io.BytesIO(blob))
    img.thumbnail((EDGE, EDGE))
    out = io.BytesIO()
    img.save(out, format="WEBP")
    return out.getvalue()


def upload(upload_id: str, blob: bytes) -> None:
    req = urllib.request.Request(
        f"{BUCKET}/{upload_id}.webp",
        data=blob,
        method="PUT",
        headers={
            "Authorization": f"Bearer {os.environ['CDN_TOKEN']}",
            "Content-Type": "image/webp",
        },
    )
    urllib.request.urlopen(req).read()


def main() -> None:
    upload_id = sys.argv[1]
    blob = thumbnail(source_bytes(upload_id))
    time.sleep(2)
    upload(upload_id, blob)


if __name__ == "__main__":
    main()
