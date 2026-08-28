from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from catalog_service.core.config import settings

engine = create_async_engine(
    url=settings.CATALOG_DB_URL,
    echo=settings.DB_ECHO,
    poolclass=NullPool if settings.TESTING else None,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)
