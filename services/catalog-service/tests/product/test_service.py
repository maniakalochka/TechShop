import uuid
from decimal import Decimal

import pytest
from catalog_service.category.model import Category
from catalog_service.product.schemas import ProductCreate
from catalog_service.product.service import CategoryNotFoundError, ProductService


class MockProductRepository:
    def __init__(self) -> None:
        self.products: dict[uuid.UUID, object] = {}

    async def get_product_by_name(self, name: str) -> None:
        return None

    async def create_product(self, product: object) -> object:
        product_id = product.id  # type: ignore[attr-defined]
        self.products[product_id] = product
        return product


class MockCategoryRepository:
    def __init__(self, category: Category | None) -> None:
        self.category = category

    async def get_category_by_id(self, category_id: uuid.UUID) -> Category | None:
        if self.category is not None and self.category.id == category_id:
            return self.category
        return None


@pytest.mark.asyncio
async def test_create_product_persists_valid_payload(category_id: uuid.UUID) -> None:
    category = Category(id=category_id, name="Gaming")
    repository = MockProductRepository()
    service = ProductService(repository, MockCategoryRepository(category))  # type: ignore[arg-type]
    payload = ProductCreate(
        name="Console",
        description="Current generation console",
        price=Decimal("499.99"),
        quantity=10,
        category_id=category_id,
    )

    product = await service.create_product(payload)

    assert product.name == "Console"
    assert product.price == Decimal("499.99")
    assert product.category_id == category_id
    assert repository.products[product.id] is product


@pytest.mark.asyncio
async def test_create_product_requires_existing_category(category_id: uuid.UUID) -> None:
    service = ProductService(MockProductRepository(), MockCategoryRepository(None))  # type: ignore[arg-type]
    payload = ProductCreate(
        name="Console",
        price=Decimal("499.99"),
        quantity=10,
        category_id=category_id,
    )

    with pytest.raises(CategoryNotFoundError):
        await service.create_product(payload)
