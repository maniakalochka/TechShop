from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from catalog_service.category.repository import CategoryRepository
from catalog_service.database.dependencies import get_async_session
from catalog_service.product.repository import ProductRepository
from catalog_service.product.service import ProductService


async def get_product_service(
    session: Annotated[AsyncSession, Depends(get_async_session)],
) -> ProductService:
    product_repository = ProductRepository(session)
    category_repository = CategoryRepository(session)
    return ProductService(
        product_repository=product_repository,
        category_repository=category_repository,
    )
