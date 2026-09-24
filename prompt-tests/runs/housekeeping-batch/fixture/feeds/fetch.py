"""Fetches every endpoint, consulting the cache first."""
import urllib.error
import urllib.request


def fetch_one(url, cache):
    hit = cache.get(url)
    if hit is not None:
        return hit
    try:
        with urllib.request.urlopen(url, timeout=5) as resp:
            row = (url, resp.status, resp.read().decode("utf-8", "replace"))
    except urllib.error.URLError as exc:
        row = (url, 0, str(exc))
    cache.put(url, row)
    return row


def fetch_all(urls, cache):
    return [fetch_one(u, cache) for u in urls]
