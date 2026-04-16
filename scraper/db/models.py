"""Database models for the KeyCRM scraper.

We keep the model definition lightweight – a Pydantic ``Order`` class mirrors the
columns of the ``orders`` table.  The raw SQL for table creation is provided as
``CREATE_ORDERS_TABLE_SQL`` so that the scraper can ensure the table exists on
first run.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field, field_validator

# ---------------------------------------------------------------------------
# Pydantic model – used for validation before persisting to PostgreSQL.
# ---------------------------------------------------------------------------

class Order(BaseModel):
    """Represents a single order extracted from KeyCRM.

    Fields:
        order_id   – unique identifier from CRM (primary key).
        created_at – date when the order was created in CRM.
        closed_at  – date when the order was closed (optional).
        status     – current order status.
        manager    – name of the responsible manager.
        total_cost – total monetary value of the order.
    """

    order_id: str = Field(..., alias="order_id")
    created_at: date = Field(..., alias="created_at")
    closed_at: Optional[date] = Field(None, alias="closed_at")
    status: str = Field(..., alias="status")
    manager: str = Field(..., alias="manager")
    total_cost: Decimal = Field(..., alias="total_cost")

    @field_validator("total_cost", mode="before")
    @classmethod
    def _coerce_decimal(cls, v):
        """Accept ``float`` or ``str`` and convert to ``Decimal`` for DB safety."""
        return Decimal(str(v))

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True

# ---------------------------------------------------------------------------
# Raw SQL for creating the ``orders`` table if it does not exist.
# ---------------------------------------------------------------------------

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
