"""Database repository utilities for persisting orders.

This module opens a ``psycopg2`` connection using the DSN from ``config``.
It ensures the ``orders`` table exists (by executing ``models.CREATE_ORDERS_TABLE_SQL``)
and provides a ``upsert_orders_batch`` function for bulk inserting/updating orders.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import List, Dict, Any

import psycopg2
from psycopg2.extras import execute_values

from .models import Order, CREATE_ORDERS_TABLE_SQL
from ..config import settings
from ..logger import log


def _get_connection():
    """Create a new ``psycopg2`` connection using the DSN from settings."""
    conn = psycopg2.connect(settings.pg_dsn)
    conn.autocommit = True
    return conn


def init_db():
    """Create the ``orders`` table if it does not already exist."""
    log.info("Initializing database – ensuring orders table exists")
    with _get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(CREATE_ORDERS_TABLE_SQL)
    log.info("Database ready")


def _normalize_order(order: Dict[str, Any]) -> tuple:
    """Convert a dict to a tuple for database insertion."""
    order_id = str(order["order_id"])
    created_at = order["created_at"]
    closed_at = order.get("closed_at")
    status = str(order["status"])
    manager = str(order["manager"])
    total_cost = Decimal(str(order["total_cost"]))
    return (order_id, created_at, closed_at, status, manager, total_cost)


def upsert_orders_batch(orders: List[Dict[str, Any]], batch_size: int = 100):
    """Insert or update multiple orders in a batch.

    Only updates status if changed, only updates total_cost if changed.
    """
    if not orders:
        return

    # SQL that only updates when values are different
    sql = """
        INSERT INTO orders (order_id, created_at, closed_at, status, manager, total_cost) 
        VALUES %s 
        ON CONFLICT (order_id) DO UPDATE SET 
            status = CASE WHEN orders.status != EXCLUDED.status THEN EXCLUDED.status ELSE orders.status END,
            total_cost = CASE WHEN orders.total_cost != EXCLUDED.total_cost THEN EXCLUDED.total_cost ELSE orders.total_cost END,
            closed_at = EXCLUDED.closed_at,
            manager = EXCLUDED.manager,
            updated_at = CASE 
                WHEN orders.status != EXCLUDED.status OR orders.total_cost != EXCLUDED.total_cost 
                THEN now() 
                ELSE orders.updated_at 
            END
    """

    values_list = [_normalize_order(order) for order in orders]

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