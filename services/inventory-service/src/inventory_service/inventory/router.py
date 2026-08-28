import uuid
from typing import Annotated, NoReturn

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from inventory_service.database.dependencies import get_async_session
from inventory_service.inventory.model import MovementType
from inventory_service.inventory.schemas import (
    AdjustmentRequest,
    MovementRead,
    QuantityRequest,
    StockRead,
)
from inventory_service.inventory.service import (
    IdempotencyConflictError,
    InactiveStockError,
    InsufficientStockError,
    InventoryService,
    StockNotFoundError,
)
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/stocks", tags=["stocks"])


def service(session: Annotated[AsyncSession, Depends(get_async_session)]) -> InventoryService:
    return InventoryService(session)


def map_error(error: Exception) -> NoReturn:
    status_code = (
        status.HTTP_404_NOT_FOUND
        if isinstance(error, StockNotFoundError)
        else status.HTTP_409_CONFLICT
    )
    detail = (
        "Stock item not found."
        if isinstance(error, StockNotFoundError)
        else "Stock operation conflicts with current state."
    )
    raise HTTPException(status_code=status_code, detail=detail) from error


@router.get("/{product_id}", response_model=StockRead)
async def get_stock(
    product_id: uuid.UUID, stock_service: Annotated[InventoryService, Depends(service)]
) -> StockRead:
    stock = await stock_service.get_stock(product_id)
    if stock is None:
        raise HTTPException(status_code=404, detail="Stock item not found.")
    return stock


@router.get("/{product_id}/movements", response_model=list[MovementRead])
async def list_movements(
    product_id: uuid.UUID,
    stock_service: Annotated[InventoryService, Depends(service)],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[MovementRead]:
    return [
        MovementRead.model_validate(movement)
        for movement in await stock_service.movements(product_id, limit, offset)
    ]


@router.post("/{product_id}/receipts", response_model=StockRead)
async def receipt(
    product_id: uuid.UUID,
    payload: QuantityRequest,
    stock_service: Annotated[InventoryService, Depends(service)],
    idempotency_key: Annotated[str, Header(alias="Idempotency-Key", min_length=1)],
) -> StockRead:
    try:
        return await stock_service.mutate(
            product_id, payload.quantity, MovementType.RECEIPT, idempotency_key, payload.reason
        )
    except (
        StockNotFoundError,
        InactiveStockError,
        InsufficientStockError,
        IdempotencyConflictError,
    ) as error:
        map_error(error)


@router.post("/{product_id}/write-offs", response_model=StockRead)
async def write_off(
    product_id: uuid.UUID,
    payload: QuantityRequest,
    stock_service: Annotated[InventoryService, Depends(service)],
    idempotency_key: Annotated[str, Header(alias="Idempotency-Key", min_length=1)],
) -> StockRead:
    try:
        return await stock_service.mutate(
            product_id, -payload.quantity, MovementType.WRITE_OFF, idempotency_key, payload.reason
        )
    except (
        StockNotFoundError,
        InactiveStockError,
        InsufficientStockError,
        IdempotencyConflictError,
    ) as error:
        map_error(error)


@router.post("/{product_id}/adjustments", response_model=StockRead)
async def adjustment(
    product_id: uuid.UUID,
    payload: AdjustmentRequest,
    stock_service: Annotated[InventoryService, Depends(service)],
    idempotency_key: Annotated[str, Header(alias="Idempotency-Key", min_length=1)],
) -> StockRead:
    try:
        return await stock_service.mutate(
            product_id,
            0,
            MovementType.ADJUSTMENT,
            idempotency_key,
            payload.reason,
            payload.target_quantity,
        )
    except (
        StockNotFoundError,
        InactiveStockError,
        InsufficientStockError,
        IdempotencyConflictError,
    ) as error:
        map_error(error)
