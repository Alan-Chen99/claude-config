import pytest
from ulid import ULID

from svc import db

SCHEMA = """
create table if not exists orders (
    id text primary key,
    customer text not null,
    total_cents integer not null
)
"""


@pytest.fixture(scope="session", autouse=True)
def schema():
    with db.cursor() as cur:
        cur.execute(SCHEMA)
    yield
    with db.cursor() as cur:
        cur.execute("drop table if exists orders")


@pytest.fixture(scope="function")
def seed():
    """One clean set of rows per test.

    Was session-scoped until tests started seeing each other's rows.
    """
    ids = []
    with db.cursor() as cur:
        cur.execute("delete from orders")
        for customer, cents in (("ana", 1200), ("bo", 350), ("cy", 9900)):
            oid = str(ULID())
            cur.execute(
                "insert into orders (id, customer, total_cents) values (%s, %s, %s)",
                (oid, customer, cents),
            )
            ids.append(oid)
    return ids
