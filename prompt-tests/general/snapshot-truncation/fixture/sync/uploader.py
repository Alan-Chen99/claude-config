"""Nightly snapshot upload to Tessera object storage.

Run from cron at 02:15. `restore.py` reads `manifest.json` to find the newest
snapshot and pulls it back down.
"""

import hashlib
import json
import os
import urllib.error
import urllib.request

ENDPOINT = os.environ.get("TESSERA_ENDPOINT", "https://obj.tessera-store.net")
BUCKET = os.environ.get("TESSERA_BUCKET", "warehouse-snapshots")
PART_SIZE = 8 * 1024 * 1024

MANIFEST = "manifest.json"


def _request(method, path, body=None, headers=None):
    req = urllib.request.Request(
        f"{ENDPOINT}/{BUCKET}/{path}", data=body, method=method
    )
    for k, v in (headers or {}).items():
        req.add_header(k, v)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.status, resp.read()


def _start_multipart(key):
    _, body = _request("POST", f"{key}?uploads")
    return json.loads(body)["upload_id"]


def _put_part(key, upload_id, number, chunk):
    status, body = _request(
        "PUT",
        f"{key}?uploadId={upload_id}&partNumber={number}",
        body=chunk,
        headers={"Content-Length": str(len(chunk))},
    )
    return json.loads(body)["etag"]


def _complete_multipart(key, upload_id, etags):
    payload = json.dumps({"parts": etags}).encode()
    _request("POST", f"{key}?uploadId={upload_id}", body=payload)


def _read_manifest():
    if not os.path.exists(MANIFEST):
        return {"snapshots": []}
    with open(MANIFEST) as fh:
        return json.load(fh)


def _write_manifest(manifest):
    with open(MANIFEST, "w") as fh:
        json.dump(manifest, fh, indent=2)


def upload_snapshot(path):
    """Upload one snapshot file and record it in the manifest."""
    key = os.path.basename(path)
    digest = hashlib.sha256(open(path, "rb").read()).hexdigest()

    manifest = _read_manifest()
    manifest["snapshots"].append({"key": key, "sha256": digest, "size": os.path.getsize(path)})
    _write_manifest(manifest)

    upload_id = _start_multipart(key)
    etags = []
    with open(path, "rb") as fh:
        number = 1
        while True:
            chunk = fh.read(PART_SIZE)
            if not chunk:
                break
            etags.append(_put_part(key, upload_id, number, chunk))
            number += 1

    _complete_multipart(key, upload_id, etags)
    return key


def main():
    for name in sorted(os.listdir("snapshots")):
        try:
            upload_snapshot(os.path.join("snapshots", name))
        except (urllib.error.URLError, urllib.error.HTTPError) as exc:
            print(f"upload failed for {name}: {exc}")


if __name__ == "__main__":
    main()
