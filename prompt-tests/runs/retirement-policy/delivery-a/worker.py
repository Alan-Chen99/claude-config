import glob
import json
import logging
import os

import purge
import render

CDN_BASE = "https://cdn.example.net/thumbs"

log = logging.getLogger(__name__)


def drain(token):
    for path in sorted(glob.glob(os.path.join("jobs", "*.json"))):
        job = json.load(open(path))
        urls = []
        for size in job["sizes"]:
            out = f"out/{job['id']}-{size}.jpg"
            render.thumb(job["src"], out, size)
            urls.append(f"{CDN_BASE}/{job['id']}-{size}.jpg")
        purge.purge(urls, token)
        # Removing the job file is what discards the only record that this
        # upload was accepted, so it happens after the purge call returns.
        os.remove(path)
        log.info("done %s", job["id"])
