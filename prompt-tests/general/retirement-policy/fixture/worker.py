import glob
import json
import os

import purge
import render

CDN_BASE = "https://cdn.example.net/thumbs"


def drain(token):
    for path in sorted(glob.glob(os.path.join("jobs", "*.json"))):
        job = json.load(open(path))
        urls = []
        for size in job["sizes"]:
            out = f"out/{job['id']}-{size}.jpg"
            render.thumb(job["src"], out, size)
            urls.append(f"{CDN_BASE}/{job['id']}-{size}.jpg")
        purge.purge(urls, token)
        os.remove(path)
        print(f"done {job['id']}")
