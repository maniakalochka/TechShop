import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager, suppress

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from catalog_service.category.router import category_router
from catalog_service.core.config import settings
from catalog_service.core.logging import get_logger
from catalog_service.database.session import AsyncSessionLocal, engine
from catalog_service.messaging.broker import broker, publish_outbox
from catalog_service.product.router import product_router

logger = get_logger("catalog_service.main")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    logger.info("Starting up...")
    app.state.engine = engine
    app.state.session_factory = AsyncSessionLocal
    if settings.TESTING:
        try:
            yield
        finally:
            await engine.dispose()
        return
    await broker.connect()
    await broker.start()
    stopped = asyncio.Event()
    task = asyncio.create_task(publish_outbox(stopped))
    try:
        logger.info("Application started successfully.")
        yield
    finally:
        stopped.set()
        task.cancel()
        with suppress(asyncio.CancelledError):
            await task
        await broker.stop()
        await engine.dispose()
        logger.info("Shutting down...")


app = FastAPI(
    title="Catalog Service",
    version="0.1.0",
    description="Product and category catalogue for TechShop.",
    lifespan=lifespan,
)


app.include_router(product_router)
app.include_router(category_router)


@app.get("/health", tags=["health"])
async def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/ready", tags=["health"])
async def readiness_check() -> dict[str, str]:
    try:
        async with engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
    except SQLAlchemyError as error:
        logger.warning("Readiness check failed: %s", error)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is unavailable.",
        ) from error
    return {"status": "ready"}


@app.exception_handler(IntegrityError)
async def integrity_error_handler(_: Request, __: IntegrityError) -> JSONResponse:
    return JSONResponse(
        status_code=409,
        content={"detail": "The requested change conflicts with existing data."},
    )
