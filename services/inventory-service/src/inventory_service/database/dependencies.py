from collections.abc import AsyncIterator

from inventory_service.database.session import AsyncSessionLocal
from sqlalchemy.ext.asyncio import AsyncSession


async def get_async_session() -> AsyncIterator[AsyncSession]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
