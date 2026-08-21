import uuid
from collections.abc import Sequence

from catalog_service.category.repository import CategoryRepository
from catalog_service.product.model import Product
from catalog_service.product.repository import ProductRepository
from catalog_service.product.schemas import ProductCreate, ProductUpdate


class ProductAlreadyExistsError(Exception):
    """Raised when a product name is already in use."""


class CategoryNotFoundError(Exception):
    """Raised when a product references a missing category."""


class ProductService:
    def __init__(
        self,
        product_repository: ProductRepository,
        category_repository: CategoryRepository,
    ):
        self.product_repository = product_repository
        self.category_repository = category_repository

    async def get_product(self, product_id: uuid.UUID) -> Product | None:
        return await self.product_repository.get_product_by_id(product_id)

    async def create_product(
        self,
        payload: ProductCreate,
    ) -> Product:
        if await self.product_repository.get_product_by_name(payload.name):
            raise ProductAlreadyExistsError
        if await self.category_repository.get_category_by_id(payload.category_id) is None:
            raise CategoryNotFoundError

        product = Product(
            name=payload.name,
            description=payload.description,
            price=payload.price,
            quantity=payload.quantity,
            category_id=payload.category_id,
        )

        return await self.product_repository.create_product(product)

    async def update_product(self, product_id: uuid.UUID, payload: ProductUpdate) -> Product | None:
        product = await self.product_repository.get_product_by_id(product_id)
        if product is None:
            return None

        updates = payload.model_dump(exclude_unset=True)
        if "name" in updates and updates["name"] != product.name:
            if await self.product_repository.get_product_by_name(updates["name"]):
                raise ProductAlreadyExistsError
        if "category_id" in updates:
            category_id = updates["category_id"]
            if await self.category_repository.get_category_by_id(category_id) is None:
                raise CategoryNotFoundError

        for field, value in updates.items():
            setattr(product, field, value)
        return await self.product_repository.update_product(product)

    async def delete_product(self, product_id: uuid.UUID) -> bool:
        product = await self.product_repository.get_product_by_id(product_id)
        if product is None:
            return False
        await self.product_repository.delete_product(product)
        return True

    async def list(self, *, limit: int, offset: int) -> Sequence[Product]:
        return await self.product_repository.list_products(limit=limit, offset=offset)
