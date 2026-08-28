import uuid
from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from techshop_contracts.events import EventEnvelope, EventType

from catalog_service.messaging.model import OutboxMessage
from catalog_service.product.model import Product


class ProductRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_product(self, product: Product) -> Product:
        self.session.add(product)
        await self.session.flush()
        event = EventEnvelope(
            event_type=EventType.CATALOG_PRODUCT_CREATED,
            correlation_id=product.id,
            payload={"product_id": str(product.id)},
        )
        self.session.add(
            OutboxMessage(routing_key=event.event_type.value, payload=event.model_dump(mode="json"))
        )
        await self.session.commit()
        await self.session.refresh(product)
        return product

    async def get_product_by_id(self, product_id: uuid.UUID) -> Product | None:
        result = await self.session.get(Product, product_id)
        return result

    async def get_product_by_name(self, name: str) -> Product | None:
        result = await self.session.execute(select(Product).where(Product.name == name))
        return result.scalar_one_or_none()

    async def update_product(self, product: Product) -> Product:
        await self.session.commit()
        await self.session.refresh(product)
        return product

    async def delete_product(self, product: Product) -> None:
        event = EventEnvelope(
            event_type=EventType.CATALOG_PRODUCT_DELETED,
            correlation_id=product.id,
            payload={"product_id": str(product.id)},
        )
        self.session.add(
            OutboxMessage(routing_key=event.event_type.value, payload=event.model_dump(mode="json"))
        )
        await self.session.delete(product)
        await self.session.commit()

    async def list_products(self, *, limit: int, offset: int) -> Sequence[Product]:
        stmt = select(Product).order_by(Product.name).limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        return result.scalars().all()
