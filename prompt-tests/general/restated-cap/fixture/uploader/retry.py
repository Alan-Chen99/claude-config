#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# ///
"""Upload parked-eligible spool directories to object storage.

Retry policy: 3 attempts, exponential backoff starting at 1 second. A job that
exhausts its attempts is moved to the parked/ directory.
"""
import argparse
import os
import pathlib
import subprocess
import sys
import tarfile
import tempfile
import time

MAX_ATTEMPTS = 3
BASE_DELAY = 1.0
TIMEOUT = float(os.environ.get("SHIPPER_TIMEOUT", "30"))
BUCKET = os.environ.get("SHIPPER_BUCKET", "renders")


def backoff(attempt: int) -> float:
    """Seconds to wait before `attempt` (1-indexed). No wait before attempt 1."""
    return 0.0 if attempt == 1 else BASE_DELAY * (2 ** (attempt - 2))


def upload(tarball: pathlib.Path, key: str) -> None:
    subprocess.run(
        ["aws", "s3", "cp", str(tarball), f"s3://{BUCKET}/{key}"],
        check=True,
        timeout=TIMEOUT,
    )


def ship(job: pathlib.Path, parked: pathlib.Path) -> bool:
    with tempfile.TemporaryDirectory() as tmp:
        tarball = pathlib.Path(tmp) / f"{job.name}.tar"
        with tarfile.open(tarball, "w") as tf:
            tf.add(job, arcname=job.name)
        for attempt in range(1, MAX_ATTEMPTS + 1):
            delay = backoff(attempt)
            if delay:
                time.sleep(delay)
            try:
                upload(tarball, f"{job.name}.tar")
                return True
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
                print(f"{job.name}: attempt {attempt}/{MAX_ATTEMPTS} failed: {e}")
    job.rename(parked / job.name)
    return False


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--spool", default=os.environ.get("SHIPPER_SPOOL", "/var/spool/shipper"))
    args = ap.parse_args()
    spool = pathlib.Path(args.spool)
    parked = spool / "parked"
    parked.mkdir(exist_ok=True)
    failures = 0
    for job in sorted(p for p in spool.iterdir() if p.is_dir() and p.name != "parked"):
        if not ship(job, parked):
            failures += 1
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
