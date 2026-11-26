import json
import os

import redis
from flask import Flask, request
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool, PoolTimeout

app = Flask(__name__)

pool = ConnectionPool(
    os.environ["DATABASE_URL"],
    min_size=2,
    max_size=int(os.getenv("POOL_MAX", "10")),
    timeout=float(os.getenv("POOL_TIMEOUT", "5")),
    check=ConnectionPool.check_connection,
    kwargs={"row_factory": dict_row, "autocommit": True},
    open=True,
)

cache_ttl = int(os.getenv("CACHE_TTL", "0"))
cache = redis.Redis.from_url(os.environ["CACHE_URL"]) if cache_ttl > 0 else None

LIST_ORDERS = """
    SELECT id, status, total, created_at
    FROM orders
    WHERE customer_id = %s
    ORDER BY created_at DESC
    LIMIT 20
"""

CREATE_ORDER = """
    INSERT INTO orders (customer_id, status, total)
    VALUES (%s, 'pending', %s)
    RETURNING id
"""


def json_response(body, status=200):
    return app.response_class(body, status=status, mimetype="application/json")


def fetch_orders_from_db(customer_id):
    with pool.connection() as conn:
        rows = conn.execute(LIST_ORDERS, (customer_id,)).fetchall()
    return json.dumps(rows, default=str)


def get_orders(customer_id):
    if cache is None:
        return fetch_orders_from_db(customer_id)

    cache_key = f"orders:{customer_id}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    body = fetch_orders_from_db(customer_id)
    cache.set(cache_key, body, ex=cache_ttl)
    return body


@app.errorhandler(PoolTimeout)
def pool_exhausted(_):
    return {"error": "database unavailable"}, 503


@app.get("/health")
def health():
    return {"status": "ok", "cache_ttl": cache_ttl}


@app.get("/orders")
def list_orders():
    customer_id = request.args.get("customer_id", type=int)
    if customer_id is None:
        return {"error": "customer_id is required"}, 400
    return json_response(get_orders(customer_id))


@app.post("/orders")
def create_order():
    data = request.get_json(silent=True) or {}
    customer_id = data.get("customer_id")
    total = data.get("total")
    if not isinstance(customer_id, int) or not isinstance(total, (int, float)):
        return {"error": "customer_id (int) and total (number) are required"}, 422

    with pool.connection() as conn:
        row = conn.execute(CREATE_ORDER, (customer_id, total)).fetchone()
    return {"id": row["id"]}, 201
