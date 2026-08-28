import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class QuantityRequest(BaseModel):
    quantity: int = Field(gt=0)
    reason: str | None = Field(default=None, max_length=255)


class AdjustmentRequest(BaseModel):
    target_quantity: int = Field(ge=0)
    reason: str | None = Field(default=None, max_length=255)


class StockRead(BaseModel):
    product_id: uuid.UUID
    available_quantity: int
    reserved_quantity: int
    total_quantity: int
    active: bool


class MovementRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    product_id: uuid.UUID
    movement_type: str
    quantity_delta: int
    available_after: int
    reserved_after: int
    source: str
    created_date: datetime
