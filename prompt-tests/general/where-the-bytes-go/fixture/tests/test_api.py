from ulid import ULID

from svc import db


def test_select_one(seed):
    row = db.select_one(seed[0])
    assert row is not None
    assert row[1] == "ana"


def test_recent_is_creation_order(seed):
    rows = db.select_recent(10)
    assert [r[0] for r in rows] == sorted(seed, reverse=True)


def test_since(seed):
    rows = db.select_since(seed[0])
    assert len(rows) == 2


def test_bulk_insert(seed):
    a, b = str(ULID()), str(ULID())
    db.insert_order(a, "dee", 1)
    db.insert_order(b, "eli", 2)
    rows = db.select_recent(2)
    assert [r[0] for r in rows] == [b, a]
