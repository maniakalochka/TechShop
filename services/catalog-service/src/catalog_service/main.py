from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from catalog_service.core.logging import get_logger
from catalog_service.database.session import AsyncSessionLocal, engine

logger = get_logger("catalog_service.main")

app = FastAPI(title="Catalog Service")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    logger.info("Starting up...")
    app.state.engine = engine
    app.state.session_factory = AsyncSessionLocal
    try:
        logger.info("Application started successfully.")
        yield
    finally:
        logger.info("Shutting down...")
