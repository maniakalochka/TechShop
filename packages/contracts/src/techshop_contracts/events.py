from __future__ import annotations

import uuid
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class RoutingKey(StrEnum):
    CATALOG_PRODUCT_CREATED = "catalog.product.created.v1"
    CATALOG_PRODUCT_DELETED = "catalog.product.deleted.v1"
    ORDER_CREATED = "order.created.v1"
    ORDER_CANCELLED = "order.cancelled.v1"
    ORDER_PAID = "order.paid.v1"
    INVENTORY_RESERVATION_CREATED = "inventory.reservation.created.v1"
    INVENTORY_RESERVATION_REJECTED = "inventory.reservation.rejected.v1"
    INVENTORY_RESERVATION_RELEASED = "inventory.reservation.released.v1"
    INVENTORY_RESERVATION_COMMITTED = "inventory.reservation.committed.v1"


class EventType(StrEnum):
    CATALOG_PRODUCT_CREATED = RoutingKey.CATALOG_PRODUCT_CREATED
    CATALOG_PRODUCT_DELETED = RoutingKey.CATALOG_PRODUCT_DELETED
    ORDER_CREATED = RoutingKey.ORDER_CREATED
    ORDER_CANCELLED = RoutingKey.ORDER_CANCELLED
    ORDER_PAID = RoutingKey.ORDER_PAID
    INVENTORY_RESERVATION_CREATED = RoutingKey.INVENTORY_RESERVATION_CREATED
    INVENTORY_RESERVATION_REJECTED = RoutingKey.INVENTORY_RESERVATION_REJECTED
    INVENTORY_RESERVATION_RELEASED = RoutingKey.INVENTORY_RESERVATION_RELEASED
    INVENTORY_RESERVATION_COMMITTED = RoutingKey.INVENTORY_RESERVATION_COMMITTED


class EventEnvelope(BaseModel):
    event_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    event_type: EventType
    occurred_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    correlation_id: uuid.UUID
    causation_id: uuid.UUID | None = None
    payload: dict[str, Any]
