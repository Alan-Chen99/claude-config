#!/usr/bin/env python3
"""Poll the configured endpoints once and print the table."""
from feeds.cache import Cache
from feeds.fetch import fetch_all
from render.table import render

ENDPOINTS = [
    "https://example.invalid/alpha",
    "https://example.invalid/beta",
]


def main():
    cache = Cache()
    rows = fetch_all(ENDPOINTS, cache)
    print(render(rows))


if __name__ == "__main__":
    main()
