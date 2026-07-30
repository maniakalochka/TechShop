from collections.abc import AsyncIterator

from catalog_service.core.logging import get_logger
from catalog_service.database.session import AsyncSessionLocal
from sqlalchemy.ext.asyncio import AsyncSession

logger = get_logger(__name__)


async def get_async_session() -> AsyncIterator[AsyncSession]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception as e:
            logger.exception("Database session error")
            await session.rollback()
            raise e
