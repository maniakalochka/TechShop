import os
import uuid
from decimal import Decimal

import pytest
import pytest_asyncio
from catalog_service.category.model import Category
from catalog_service.category.repository import CategoryRepository
from catalog_service.database.session import AsyncSessionLocal
from catalog_service.product.model import Product
from catalog_service.product.repository import ProductRepository
from sqlalchemy import delete

pytestmark = pytest.mark.integration


@pytest_asyncio.fixture(autouse=True)
async def clean_database() -> None:
    if os.getenv("RUN_DB_TESTS") != "true":
        pytest.skip("Set RUN_DB_TESTS=true to run PostgreSQL integration tests.")
    async with AsyncSessionLocal() as session:
        await session.execute(delete(Product))
        await session.execute(delete(Category))
        await session.commit()


@pytest.mark.asyncio
async def test_repository_commits_product_and_preserves_decimal_price() -> None:
    category_id = uuid.uuid4()
    async with AsyncSessionLocal() as session:
        category_repository = CategoryRepository(session)
        category = await category_repository.create_category(
            Category(id=category_id, name="Gaming")
        )
        product = await ProductRepository(session).create_product(
            Product(
                name="Console",
                description="Current generation console",
                price=Decimal("499.99"),
                category_id=category.id,
            )
        )

    async with AsyncSessionLocal() as session:
        loaded = await ProductRepository(session).get_product_by_id(product.id)

    assert loaded is not None
    assert loaded.price == Decimal("499.99")
    assert loaded.category_id == category_id
