"""Connection pool and every statement that reaches Postgres."""

import os
from contextlib import contextmanager

import psycopg
from psycopg_pool import ConnectionPool

DATABASE_URL = os.environ.get(
    "DATABASE_URL", "postgresql://svc:svc@127.0.0.1:5432/svc_test"
)

_pool = ConnectionPool(DATABASE_URL, min_size=1, max_size=8, open=False)


@contextmanager
def cursor():
    with _pool.connection() as conn:
        with conn.cursor(name="svc") as cur:
            yield cur


def insert_order(order_id: str, customer: str, total_cents: int) -> None:
    with cursor() as cur:
        cur.execute(
            "insert into orders (id, customer, total_cents) values (%s, %s, %s)",
            (order_id, customer, total_cents),
        )


def select_recent(limit: int) -> list[tuple]:
    # id is a ULID: lexicographic order is creation order.
    with cursor() as cur:
        cur.execute("select id, customer, total_cents from orders order by id desc limit %s", (limit,))
        return cur.fetchall()


def select_since(order_id: str) -> list[tuple]:
    with cursor() as cur:
        cur.execute("select id, customer, total_cents from orders where id > %s order by id", (order_id,))
        return cur.fetchall()


def select_one(order_id: str) -> tuple | None:
    with cursor() as cur:
        cur.execute("select id, customer, total_cents from orders where id = %s", (order_id,))
        return cur.fetchone()
