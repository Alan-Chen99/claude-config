"""HTTP client for Kestrel's SMS API."""

import os
import time
import uuid

import requests

BASE = os.environ.get("KESTREL_BASE", "https://api.kestrel.example/v1")
TIMEOUT = 5
RETRIES = 3
BACKOFF = 2.0


def send(to: str, body: str) -> str:
    """Send one message. Returns Kestrel's message id."""
    payload = {"to": to, "body": body}
    last = None
    for _ in range(RETRIES):
        headers = {
            "Authorization": f"Bearer {os.environ['KESTREL_TOKEN']}",
            "Idempotency-Key": str(uuid.uuid4()),
        }
        try:
            r = requests.post(
                f"{BASE}/messages", json=payload, headers=headers, timeout=TIMEOUT
            )
        except requests.RequestException as exc:
            last = exc
        else:
            if r.status_code < 500:
                r.raise_for_status()
                return r.json()["message_id"]
            last = requests.HTTPError(f"{r.status_code} {r.text[:200]}")
        time.sleep(BACKOFF)
    raise RuntimeError(f"kestrel send failed after {RETRIES} attempts: {last}")
