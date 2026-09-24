"""In-memory response cache keyed by URL."""
import time

TTL_SECONDS = 900


class Cache:
    def __init__(self, ttl=TTL_SECONDS):
        self._ttl = ttl
        self._entries = {}

    def get(self, url):
        entry = self._entries.get(url)
        if entry is None:
            return None
        stored_at, value = entry
        if time.monotonic() - stored_at > self._ttl:
            del self._entries[url]
            return None
        return value

    def put(self, url, value):
        self._entries[url] = (time.monotonic(), value)
