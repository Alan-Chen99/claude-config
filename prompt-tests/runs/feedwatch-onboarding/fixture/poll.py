"""Polls the upstream feed and hands new entries to the store."""

import time

import feedparser
import httpx

import store
from retry import call_with_retry

FEED_URL = "https://example.invalid/feed.atom"
INTERVAL_SECONDS = 90


def fetch():
    r = httpx.get(FEED_URL, timeout=10.0)
    r.raise_for_status()
    return feedparser.parse(r.text)


def run():
    while True:
        parsed = call_with_retry(fetch)
        for entry in parsed.entries:
            store.put(entry.id, entry.title, entry.updated)
        time.sleep(INTERVAL_SECONDS)


if __name__ == "__main__":
    run()
