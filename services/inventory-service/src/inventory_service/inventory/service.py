from __future__ import annotations

import hashlib
import json
import uuid
from datetime import UTC, datetime, timedelta

from inventory_service.core.config import settings
from inventory_service.inventory.model import (
    InboxMessage,
    MovementType,
    OutboxMessage,
    RequestDeduplication,
    Reservation,
    ReservationItem,
    ReservationStatus,
    StockBalance,
    StockMovement,
)
from inventory_service.inventory.schemas import StockRead
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from techshop_contracts.events import EventEnvelope, EventType


class InventoryError(Exception):
    pass


class StockNotFoundError(InventoryError):
    pass


class InactiveStockError(InventoryError):
    pass


class InsufficientStockError(InventoryError):
    pass


class IdempotencyConflictError(InventoryError):
    pass


class InventoryService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    @staticmethod
    def _read(balance: StockBalance) -> StockRead:
        return StockRead(
            product_id=balance.product_id,
            available_quantity=balance.available_quantity,
            reserved_quantity=balance.reserved_quantity,
            total_quantity=balance.available_quantity + balance.reserved_quantity,
            active=balance.active,
        )

    async def get_stock(self, product_id: uuid.UUID) -> StockRead | None:
        balance = await self.session.get(StockBalance, product_id)
        return self._read(balance) if balance else None

    async def movements(
        self, product_id: uuid.UUID, limit: int, offset: int
    ) -> list[StockMovement]:
        result = await self.session.execute(
            select(StockMovement)
            .where(StockMovement.product_id == product_id)
            .order_by(StockMovement.created_date.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars())

    async def _locked_balance(self, product_id: uuid.UUID) -> StockBalance:
        result = await self.session.execute(
            select(StockBalance).where(StockBalance.product_id == product_id).with_for_update()
        )
        balance = result.scalar_one_or_none()
        if balance is None:
            raise StockNotFoundError
        if not balance.active:
            raise InactiveStockError
        return balance

    async def _idempotent(self, key: str, request: dict[str, object]) -> dict[str, object] | None:
        fingerprint = hashlib.sha256(
            json.dumps(request, sort_keys=True, default=str).encode()
        ).hexdigest()
        row = await self.session.get(RequestDeduplication, key)
        if row is None:
            return None
        if row.request_fingerprint != fingerprint:
            raise IdempotencyConflictError
        return row.response

    async def mutate(
        self,
        product_id: uuid.UUID,
        quantity_delta: int,
        movement_type: MovementType,
        key: str,
        reason: str | None = None,
        target_quantity: int | None = None,
    ) -> StockRead:
        request = {
            "product_id": str(product_id),
            "quantity_delta": quantity_delta,
            "movement_type": movement_type,
            "reason": reason,
            "target_quantity": target_quantity,
        }
        existing = await self._idempotent(key, request)
        if existing is not None:
            return StockRead.model_validate(existing)
        balance = await self._locked_balance(product_id)
        if target_quantity is not None:
            if target_quantity < balance.reserved_quantity:
                raise InsufficientStockError
            quantity_delta = target_quantity - (
                balance.available_quantity + balance.reserved_quantity
            )
        if balance.available_quantity + quantity_delta < 0:
            raise InsufficientStockError
        balance.available_quantity += quantity_delta
        balance.version += 1
        self.session.add(
            StockMovement(
                product_id=product_id,
                movement_type=movement_type,
                quantity_delta=quantity_delta,
                available_after=balance.available_quantity,
                reserved_after=balance.reserved_quantity,
                reference_key=key,
                source="http",
            )
        )
        response = self._read(balance).model_dump(mode="json")
        fingerprint = hashlib.sha256(
            json.dumps(request, sort_keys=True, default=str).encode()
        ).hexdigest()
        self.session.add(
            RequestDeduplication(
                idempotency_key=key, request_fingerprint=fingerprint, response=response
            )
        )
        await self.session.commit()
        return StockRead.model_validate(response)

    async def handle_catalog_product(self, event: EventEnvelope, deleted: bool) -> None:
        if await self._seen("catalog-product", event.event_id):
            return
        product_id = uuid.UUID(str(event.payload["product_id"]))
        balance = await self.session.get(StockBalance, product_id, with_for_update=True)
        if balance is None:
            balance = StockBalance(product_id=product_id, active=not deleted)
            self.session.add(balance)
        elif deleted:
            balance.active = False
        await self._mark_seen("catalog-product", event.event_id)
        await self.session.commit()

    async def reserve(self, event: EventEnvelope) -> None:
        if await self._seen("order-reservation", event.event_id):
            return
        order_id = uuid.UUID(str(event.payload["order_id"]))
        existing = await self.session.scalar(
            select(Reservation).where(Reservation.order_id == order_id)
        )
        if existing is not None:
            await self._mark_seen("order-reservation", event.event_id)
            await self.session.commit()
            return
        items = event.payload["items"]
        assert isinstance(items, list)
        product_ids = [
            uuid.UUID(str(item["product_id"])) for item in items if isinstance(item, dict)
        ]
        balances = {
            balance.product_id: balance
            for balance in (
                await self.session.execute(
                    select(StockBalance)
                    .where(StockBalance.product_id.in_(product_ids))
                    .with_for_update()
                )
            ).scalars()
        }
        shortages: list[dict[str, object]] = []
        for item in items:
            assert isinstance(item, dict)
            product_id, quantity = uuid.UUID(str(item["product_id"])), int(item["quantity"])
            balance = balances.get(product_id)
            if balance is None or not balance.active or balance.available_quantity < quantity:
                shortages.append(
                    {
                        "product_id": str(product_id),
                        "requested_quantity": quantity,
                        "available_quantity": balance.available_quantity if balance else 0,
                    }
                )
        if shortages:
            reservation = Reservation(
                order_id=order_id, status=ReservationStatus.REJECTED, expires_at=datetime.now(UTC)
            )
            self.session.add(reservation)
            self._event(
                EventType.INVENTORY_RESERVATION_REJECTED,
                event,
                {"order_id": str(order_id), "shortages": shortages},
            )
        else:
            expires_at = datetime.now(UTC) + timedelta(
                seconds=settings.INVENTORY_RESERVATION_TTL_SECONDS
            )
            reservation = Reservation(
                order_id=order_id, status=ReservationStatus.ACTIVE, expires_at=expires_at
            )
            self.session.add(reservation)
            for item in items:
                assert isinstance(item, dict)
                product_id, quantity = uuid.UUID(str(item["product_id"])), int(item["quantity"])
                balance = balances[product_id]
                balance.available_quantity -= quantity
                balance.reserved_quantity += quantity
                balance.version += 1
                reservation.items.append(ReservationItem(product_id=product_id, quantity=quantity))
                self.session.add(
                    StockMovement(
                        product_id=product_id,
                        movement_type=MovementType.RESERVATION,
                        quantity_delta=-quantity,
                        available_after=balance.available_quantity,
                        reserved_after=balance.reserved_quantity,
                        reference_key=f"reservation:{order_id}:{product_id}",
                        source="order",
                    )
                )
            self._event(
                EventType.INVENTORY_RESERVATION_CREATED,
                event,
                {"order_id": str(order_id), "expires_at": expires_at.isoformat(), "items": items},
            )
        await self._mark_seen("order-reservation", event.event_id)
        await self.session.commit()

    async def transition(
        self,
        event: EventEnvelope,
        commit: bool,
        release_reason: str = "cancelled",
    ) -> None:
        consumer = "order-payment" if commit else "order-cancellation"
        if await self._seen(consumer, event.event_id):
            return
        order_id = uuid.UUID(str(event.payload["order_id"]))
        reservation = await self.session.scalar(
            select(Reservation).where(Reservation.order_id == order_id).with_for_update()
        )
        if reservation is not None and reservation.status == ReservationStatus.ACTIVE:
            balances = {
                b.product_id: b
                for b in (
                    await self.session.execute(
                        select(StockBalance)
                        .where(
                            StockBalance.product_id.in_([i.product_id for i in reservation.items])
                        )
                        .with_for_update()
                    )
                ).scalars()
            }
            for item in reservation.items:
                balance = balances[item.product_id]
                balance.reserved_quantity -= item.quantity
                if not commit:
                    balance.available_quantity += item.quantity
                balance.version += 1
                self.session.add(
                    StockMovement(
                        product_id=item.product_id,
                        movement_type=MovementType.COMMIT if commit else MovementType.RELEASE,
                        quantity_delta=item.quantity if not commit else 0,
                        available_after=balance.available_quantity,
                        reserved_after=balance.reserved_quantity,
                        reference_key=f"{'commit' if commit else 'release'}:{order_id}:{item.product_id}",
                        source="order",
                    )
                )
            reservation.status = (
                ReservationStatus.COMMITTED if commit else ReservationStatus.RELEASED
            )
            self._event(
                EventType.INVENTORY_RESERVATION_COMMITTED
                if commit
                else EventType.INVENTORY_RESERVATION_RELEASED,
                event,
                {"order_id": str(order_id), "reason": "paid" if commit else release_reason},
            )
        await self._mark_seen(consumer, event.event_id)
        await self.session.commit()

    async def expire(self) -> int:
        result = await self.session.execute(
            select(Reservation)
            .where(
                Reservation.status == ReservationStatus.ACTIVE,
                Reservation.expires_at <= datetime.now(UTC),
            )
            .with_for_update(skip_locked=True)
        )
        reservations = list(result.scalars())
        for reservation in reservations:
            event = EventEnvelope(
                event_type=EventType.ORDER_CANCELLED,
                correlation_id=reservation.order_id,
                payload={"order_id": str(reservation.order_id)},
            )
            await self.transition(event, commit=False, release_reason="expired")
            reservation.status = ReservationStatus.EXPIRED
        await self.session.commit()
        return len(reservations)

    async def _seen(self, consumer: str, event_id: uuid.UUID) -> bool:
        return (
            await self.session.scalar(
                select(InboxMessage.id).where(
                    InboxMessage.consumer_name == consumer, InboxMessage.event_id == event_id
                )
            )
            is not None
        )

    async def _mark_seen(self, consumer: str, event_id: uuid.UUID) -> None:
        self.session.add(InboxMessage(consumer_name=consumer, event_id=event_id))

    def _event(
        self, event_type: EventType, cause: EventEnvelope, payload: dict[str, object]
    ) -> None:
        event = EventEnvelope(
            event_type=event_type,
            correlation_id=cause.correlation_id,
            causation_id=cause.event_id,
            payload=payload,
        )
        self.session.add(
            OutboxMessage(routing_key=event_type.value, payload=event.model_dump(mode="json"))
        )
