"""HTTP surface."""

from fastapi import FastAPI, HTTPException
from ulid import ULID

from . import db

app = FastAPI()


@app.post("/orders")
def create_order(customer: str, total_cents: int) -> dict:
    order_id = str(ULID())
    db.insert_order(order_id, customer, total_cents)
    return {"id": order_id}


@app.get("/orders/{order_id}")
def get_order(order_id: str) -> dict:
    row = db.select_one(order_id)
    if row is None:
        raise HTTPException(status_code=404)
    return {"id": row[0], "customer": row[1], "total_cents": row[2]}


@app.get("/orders")
def recent(limit: int = 20) -> list[dict]:
    return [
        {"id": r[0], "customer": r[1], "total_cents": r[2]}
        for r in db.select_recent(limit)
    ]
