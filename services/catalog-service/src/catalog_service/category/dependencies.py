from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from catalog_service.category.service import CategoryService
from catalog_service.database.dependencies import get_async_session


async def get_category_service(
    session: Annotated[AsyncSession, Depends(get_async_session)],
) -> CategoryService:
    from catalog_service.category.repository import CategoryRepository

    return CategoryService(CategoryRepository(session))
