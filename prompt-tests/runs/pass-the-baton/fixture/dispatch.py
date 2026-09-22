#!/usr/bin/env python3
"""dispatch — move rows from the outbox to Truxel."""
import logging
import os
import time

import httpx
import psycopg

POLL_SECONDS = 300
REQUEST_TIMEOUT = 10.0
MAX_ATTEMPTS = 4
BACKOFF_BASE = 2.0
BATCH = 200

TRUXEL_URL = os.environ["TRUXEL_URL"].rstrip("/") + "/v1/shipments"
TRUXEL_KEY = os.environ["TRUXEL_KEY"]
DSN = os.environ["DISPATCH_DSN"]

log = logging.getLogger("dispatch")


def claim_batch(conn):
    with conn.cursor() as cur:
        cur.execute(
            "SELECT id, order_id, payload FROM outbox "
            "WHERE shipped_at IS NULL ORDER BY created_at LIMIT %s",
            (BATCH,),
        )
        return cur.fetchall()


def send(client, order_id, payload):
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            resp = client.post(
                TRUXEL_URL,
                json=payload,
                headers={
                    "Authorization": f"Bearer {TRUXEL_KEY}",
                    "Idempotency-Key": str(order_id),
                },
                timeout=REQUEST_TIMEOUT,
            )
        except httpx.TimeoutException:
            log.warning("order %s attempt %s timed out", order_id, attempt)
        else:
            if resp.status_code < 500:
                resp.raise_for_status()
                return resp.json()["tracking"]
            log.warning("order %s attempt %s: HTTP %s", order_id, attempt, resp.status_code)
        if attempt < MAX_ATTEMPTS:
            time.sleep(BACKOFF_BASE ** attempt)
    return None


def record(conn, row_id, order_id, tracking):
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO shipments (order_id, tracking) VALUES (%s, %s) "
            "ON CONFLICT DO NOTHING",
            (order_id, tracking),
        )
        cur.execute("UPDATE outbox SET shipped_at = now() WHERE id = %s", (row_id,))
    conn.commit()


def cycle(conn, client):
    for row_id, order_id, payload in claim_batch(conn):
        tracking = send(client, order_id, payload)
        if tracking is None:
            log.error("order %s left in the outbox", order_id)
            continue
        record(conn, row_id, order_id, tracking)


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    with psycopg.connect(DSN) as conn, httpx.Client() as client:
        while True:
            cycle(conn, client)
            time.sleep(POLL_SECONDS)


if __name__ == "__main__":
    main()
