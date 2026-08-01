import uuid
from collections.abc import Sequence

from catalog_service.product.model import Product
from catalog_service.product.repository import ProductRepository


class ProductService:
    def __init__(self, product_repository: ProductRepository):
        self.product_repository = product_repository

    async def get_product(self, product_id: uuid.UUID) -> Product | None:
        return await self.product_repository.get_product_by_id(product_id)

    async def create_product(self, product_data: Product) -> Product:
        return await self.product_repository.create_product(product_data)

    async def list(self) -> Sequence[Product]:
        return await self.product_repository.list_products()
