from __future__ import annotations

import uuid
from datetime import datetime
from enum import StrEnum

from inventory_service.database.base import Base
from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship


class MovementType(StrEnum):
    RECEIPT = "receipt"
    WRITE_OFF = "write_off"
    ADJUSTMENT = "adjustment"
    RESERVATION = "reservation"
    RELEASE = "release"
    COMMIT = "commit"


class ReservationStatus(StrEnum):
    ACTIVE = "active"
    RELEASED = "released"
    COMMITTED = "committed"
    REJECTED = "rejected"
    EXPIRED = "expired"


class StockBalance(Base):
    __tablename__ = "stock_balances"
    __table_args__ = (
        CheckConstraint("available_quantity >= 0", name="available_non_negative"),
        CheckConstraint("reserved_quantity >= 0", name="reserved_non_negative"),
    )
    product_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    available_quantity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    reserved_quantity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)


class StockMovement(Base):
    __tablename__ = "stock_movements"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    movement_type: Mapped[str] = mapped_column(String(32), nullable=False)
    quantity_delta: Mapped[int] = mapped_column(Integer, nullable=False)
    available_after: Mapped[int] = mapped_column(Integer, nullable=False)
    reserved_after: Mapped[int] = mapped_column(Integer, nullable=False)
    reference_key: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    source: Mapped[str] = mapped_column(String(64), nullable=False)


class RequestDeduplication(Base):
    __tablename__ = "request_deduplications"
    idempotency_key: Mapped[str] = mapped_column(String(255), primary_key=True)
    request_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    response: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False)


class Reservation(Base):
    __tablename__ = "reservations"
    __table_args__ = (UniqueConstraint("order_id", name="uq_reservations_order_id"),)
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    items: Mapped[list[ReservationItem]] = relationship(cascade="all, delete-orphan")


class ReservationItem(Base):
    __tablename__ = "reservation_items"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    reservation_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("reservations.id"), nullable=False)
    product_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)


class InboxMessage(Base):
    __tablename__ = "inbox_messages"
    __table_args__ = (
        UniqueConstraint("consumer_name", "event_id", name="uq_inbox_consumer_event"),
    )
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    consumer_name: Mapped[str] = mapped_column(String(128), nullable=False)
    event_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)


class OutboxMessage(Base):
    __tablename__ = "outbox_messages"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    routing_key: Mapped[str] = mapped_column(String(255), nullable=False)
    payload: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
