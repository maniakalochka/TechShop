from __future__ import annotations

import asyncio
from contextlib import suppress

from faststream.rabbit import ExchangeType, RabbitBroker, RabbitExchange, RabbitQueue
from inventory_service.core.config import settings
from inventory_service.database.session import AsyncSessionLocal
from inventory_service.inventory.model import OutboxMessage
from inventory_service.inventory.service import InventoryService
from sqlalchemy import select
from techshop_contracts.events import EventEnvelope, RoutingKey

exchange = RabbitExchange("techshop.events", type=ExchangeType.TOPIC, durable=True)
broker = RabbitBroker(settings.RABBITMQ_URL)


async def _handle(message: dict[str, object], handler: str) -> None:
    event = EventEnvelope.model_validate(message)
    async with AsyncSessionLocal() as session:
        service = InventoryService(session)
        if handler == "created":
            await service.handle_catalog_product(event, deleted=False)
        elif handler == "deleted":
            await service.handle_catalog_product(event, deleted=True)
        elif handler == "reserve":
            await service.reserve(event)
        elif handler == "cancel":
            await service.transition(event, commit=False)
        else:
            await service.transition(event, commit=True)


@broker.subscriber(
    RabbitQueue(
        "inventory.catalog.created", durable=True, routing_key=RoutingKey.CATALOG_PRODUCT_CREATED
    ),
    exchange=exchange,
)
async def catalog_created(message: dict[str, object]) -> None:
    await _handle(message, "created")


@broker.subscriber(
    RabbitQueue(
        "inventory.catalog.deleted", durable=True, routing_key=RoutingKey.CATALOG_PRODUCT_DELETED
    ),
    exchange=exchange,
)
async def catalog_deleted(message: dict[str, object]) -> None:
    await _handle(message, "deleted")


@broker.subscriber(
    RabbitQueue("inventory.order.created", durable=True, routing_key=RoutingKey.ORDER_CREATED),
    exchange=exchange,
)
async def order_created(message: dict[str, object]) -> None:
    await _handle(message, "reserve")


@broker.subscriber(
    RabbitQueue("inventory.order.cancelled", durable=True, routing_key=RoutingKey.ORDER_CANCELLED),
    exchange=exchange,
)
async def order_cancelled(message: dict[str, object]) -> None:
    await _handle(message, "cancel")


@broker.subscriber(
    RabbitQueue("inventory.order.paid", durable=True, routing_key=RoutingKey.ORDER_PAID),
    exchange=exchange,
)
async def order_paid(message: dict[str, object]) -> None:
    await _handle(message, "paid")


async def publish_outbox(stop: asyncio.Event) -> None:
    while not stop.is_set():
        async with AsyncSessionLocal() as session:
            messages = list(
                (
                    await session.execute(
                        select(OutboxMessage)
                        .where(OutboxMessage.published_at.is_(None))
                        .order_by(OutboxMessage.created_date)
                        .limit(100)
                        .with_for_update(skip_locked=True)
                    )
                ).scalars()
            )
            for message in messages:
                message.attempts += 1
                await broker.publish(
                    message.payload,
                    exchange=exchange,
                    routing_key=message.routing_key,
                    persist=True,
                    message_id=str(message.id),
                )
                from datetime import UTC, datetime

                message.published_at = datetime.now(UTC)
            await session.commit()
        with suppress(TimeoutError):
            await asyncio.wait_for(stop.wait(), timeout=1)


async def expire_reservations(stop: asyncio.Event) -> None:
    while not stop.is_set():
        async with AsyncSessionLocal() as session:
            await InventoryService(session).expire()
        with suppress(TimeoutError):
            await asyncio.wait_for(stop.wait(), timeout=30)
