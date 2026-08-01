import uuid
from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from catalog_service.product.model import Product


class ProductRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_product(self, product: Product) -> Product:
        self.session.add(product)
        await self.session.flush()
        return product

    async def get_product_by_id(self, product_id: uuid.UUID) -> Product | None:
        result = await self.session.get(Product, product_id)
        return result

    async def list_products(self) -> Sequence[Product]:
        stmt = select(Product)
        result = await self.session.execute(stmt)
        return result.scalars().all()
