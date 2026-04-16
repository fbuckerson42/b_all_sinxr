"""Database repository utilities for persisting orders.

This module opens a ``psycopg2`` connection using the DSN from ``config``.
It ensures the ``orders`` table exists (by executing ``models.CREATE_ORDERS_TABLE_SQL``)
and provides a ``upsert_orders_batch`` function for bulk inserting/updating orders.
"""

from __future__ import annotations

from typing import List, Mapping, Union

import psycopg2
from psycopg2.extras import execute_values

from .models import Order, CREATE_ORDERS_TABLE_SQL
from ..config import settings
from ..logger import log

# ---------------------------------------------------------------------------
# Helper to obtain a new connection – callers are responsible for closing it.
# ---------------------------------------------------------------------------

def _get_connection():
    """Create a new ``psycopg2`` connection using the DSN from settings.

    The connection uses ``autocommit`` so that each UPSERT is persisted
    immediately – this keeps the scraper simple and avoids transaction
    boilerplate.
    """
    conn = psycopg2.connect(settings.pg_dsn)
    conn.autocommit = True
    return conn

# ---------------------------------------------------------------------------
# Initialise the database – executed once per process start.
# ---------------------------------------------------------------------------

def init_db():
    """Create the ``orders`` table if it does not already exist."""
    log.info("Initializing database – ensuring orders table exists")
    with _get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(CREATE_ORDERS_TABLE_SQL)
    log.info("Database ready")


def upsert_orders_batch(orders: List[Union[Order, Mapping]], batch_size: int = 100):
    """Insert or update multiple orders in a batch.

    Parameters
    ----------
    orders: List of ``Order`` or mapping with keys matching the ``Order`` fields.
    batch_size: Number of orders to insert per batch (default 100).
    """
    if not orders:
        return

    sql = (
        "INSERT INTO orders (order_id, created_at, closed_at, status, manager, total_cost) "
        "VALUES %s ON CONFLICT (order_id) DO UPDATE SET "
        "created_at = EXCLUDED.created_at, "
        "closed_at = EXCLUDED.closed_at, "
        "status = EXCLUDED.status, "
        "manager = EXCLUDED.manager, "
        "total_cost = EXCLUDED.total_cost, "
        "updated_at = now();"
    )

    normalized_orders = []
    for order in orders:
        if not isinstance(order, Order):
            order = Order(**order)
        normalized_orders.append(order)

    values_list = [
        (o.order_id, o.created_at, o.closed_at, o.status, o.manager, o.total_cost)
        for o in normalized_orders
    ]

    try:
        with _get_connection() as conn:
            with conn.cursor() as cur:
                for i in range(0, len(values_list), batch_size):
                    batch = values_list[i:i + batch_size]
                    execute_values(cur, sql, batch)
        log.info("Upserted orders batch", count=len(orders))
    except Exception as exc:
        log.error("Failed to upsert orders batch", error=str(exc), count=len(orders))
        raise
