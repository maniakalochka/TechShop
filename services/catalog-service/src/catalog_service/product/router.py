import uuid
from collections.abc import Sequence
from typing import Annotated

from fastapi import APIRouter, Depends, status

from catalog_service.product.dependencies import get_product_service
from catalog_service.product.model import Product
from catalog_service.product.schemas import Product as ProductSchema
from catalog_service.product.service import ProductService

product_router = APIRouter(prefix="/", tags=["products"])


@product_router.post("", response_model=ProductSchema, status_code=status.HTTP_201_CREATED)
async def create_product(
    payload: Product, service: Annotated[ProductService, Depends(get_product_service)]
) -> Product:
    product = await service.create_product(payload)
    return product


@product_router.get("{product_id}", response_model=ProductSchema, status_code=status.HTTP_200_OK)
async def get_product(
    product_id: uuid.UUID, service: Annotated[ProductService, Depends(get_product_service)]
) -> Product | None:
    product = await service.get_product(product_id)
    return product


@product_router.get("list", response_model=list[ProductSchema], status_code=status.HTTP_200_OK)
async def list_products(
    service: Annotated[ProductService, Depends(get_product_service)],
) -> Sequence[Product]:
    products = await service.list()
    return products
