import glob
import json
import logging
import os

import purge
import render

logger = logging.getLogger(__name__)

CDN_BASE = "https://cdn.example.net/thumbs"


def drain(token):
    """Render and purge every accepted job, oldest id first.

    A job file is removed only once its thumbnails are rendered and the CDN
    purge has returned. If either step raises, the file stays and the job is
    retried on the next drain, so this function is the only thing permitted to
    delete from jobs/. See jobs/README.md.
    """
    for path in sorted(glob.glob(os.path.join("jobs", "*.json"))):
        with open(path) as fh:
            job = json.load(fh)
        urls = []
        for size in job["sizes"]:
            out = f"out/{job['id']}-{size}.jpg"
            render.thumb(job["src"], out, size)
            urls.append(f"{CDN_BASE}/{job['id']}-{size}.jpg")
        purge.purge(urls, token)
        os.remove(path)
        logger.info("done %s", job["id"])
