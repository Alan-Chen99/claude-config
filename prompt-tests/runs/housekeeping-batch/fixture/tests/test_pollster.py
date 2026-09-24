from feeds.cache import Cache
from render.table import render


def test_cache_returns_none_for_miss():
    assert Cache().get("https://example.invalid/alpha") is None


def test_cache_round_trip():
    c = Cache()
    row = ("https://example.invalid/alpha", 200, "ok")
    c.put(row[0], row)
    assert c.get(row[0]) == row


def test_render_aligns_columns():
    rows = [
        ("https://example.invalid/alpha", 200, "ok"),
        ("https://example.invalid/b", 500, "boom"),
    ]
    lines = render(rows).splitlines()
    assert len({len(l) for l in lines}) == 1
