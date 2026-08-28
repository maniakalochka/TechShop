from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager, suppress

from fastapi import FastAPI, HTTPException, status
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from inventory_service.database.session import engine
from inventory_service.inventory.router import router
from inventory_service.messaging.broker import broker, expire_reservations, publish_outbox


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    await broker.connect()
    await broker.start()
    stopped = asyncio.Event()
    outbox_task = asyncio.create_task(publish_outbox(stopped))
    expiry_task = asyncio.create_task(expire_reservations(stopped))
    try:
        yield
    finally:
        stopped.set()
        outbox_task.cancel()
        expiry_task.cancel()
        with suppress(asyncio.CancelledError):
            await outbox_task
        with suppress(asyncio.CancelledError):
            await expiry_task
        await broker.stop()
        await engine.dispose()


app = FastAPI(title="Inventory Service", version="0.1.0", lifespan=lifespan)
app.include_router(router)


@app.get("/health", tags=["health"])
async def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/ready", tags=["health"])
async def readiness_check() -> dict[str, str]:
    try:
        async with engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
    except SQLAlchemyError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database is unavailable."
        ) from error
    return {"status": "ready"}
