import asyncio
from contextlib import suppress
from datetime import UTC, datetime

from faststream.rabbit import ExchangeType, RabbitBroker, RabbitExchange
from sqlalchemy import select

from catalog_service.core.config import settings
from catalog_service.database.session import AsyncSessionLocal
from catalog_service.messaging.model import OutboxMessage

exchange = RabbitExchange("techshop.events", type=ExchangeType.TOPIC, durable=True)
broker = RabbitBroker(settings.RABBITMQ_URL)


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
                message.published_at = datetime.now(UTC)
            await session.commit()
        with suppress(TimeoutError):
            await asyncio.wait_for(stop.wait(), timeout=1)
