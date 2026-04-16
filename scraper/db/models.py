"""Database models for the KeyCRM scraper.

Simple classes for orders without pydantic dependency.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Optional


@dataclass
class Order:
    """Represents a single order extracted from KeyCRM."""

    order_id: str
    created_at: date
    closed_at: Optional[date]
    status: str
    manager: str
    total_cost: Decimal


CREATE_ORDERS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS orders (
    order_id      TEXT PRIMARY KEY,
    created_at    DATE NOT NULL,
    closed_at     DATE,
    status        TEXT NOT NULL,
    manager       TEXT NOT NULL,
    total_cost    NUMERIC(12,2) NOT NULL,
    updated_at    TIMESTAMP WITH TIME ZONE DEFAULT now()
);
"""