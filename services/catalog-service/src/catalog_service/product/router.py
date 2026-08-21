import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status

from catalog_service.product.dependencies import get_product_service
from catalog_service.product.schemas import ProductCreate, ProductRead, ProductUpdate
from catalog_service.product.service import (
    CategoryNotFoundError,
    ProductAlreadyExistsError,
    ProductService,
)

product_router = APIRouter(prefix="/products", tags=["products"])


@product_router.post("", response_model=ProductRead, status_code=status.HTTP_201_CREATED)
async def create_product(
    payload: ProductCreate,
    service: Annotated[ProductService, Depends(get_product_service)],
) -> ProductRead:
    try:
        product = await service.create_product(payload)
    except ProductAlreadyExistsError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Product name already exists.",
        ) from error
    except CategoryNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found.",
        ) from error
    return ProductRead.model_validate(product)


@product_router.get("", response_model=list[ProductRead])
async def list_products(
    service: Annotated[ProductService, Depends(get_product_service)],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[ProductRead]:
    products = await service.list(limit=limit, offset=offset)
    return [ProductRead.model_validate(product) for product in products]


@product_router.get("/{product_id}", response_model=ProductRead)
async def get_product(
    product_id: uuid.UUID,
    service: Annotated[ProductService, Depends(get_product_service)],
) -> ProductRead:
    product = await service.get_product(product_id)
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found.")
    return ProductRead.model_validate(product)


@product_router.patch("/{product_id}", response_model=ProductRead)
async def update_product(
    product_id: uuid.UUID,
    payload: ProductUpdate,
    service: Annotated[ProductService, Depends(get_product_service)],
) -> ProductRead:
    try:
        product = await service.update_product(product_id, payload)
    except ProductAlreadyExistsError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Product name already exists.",
        ) from error
    except CategoryNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found.",
        ) from error
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found.")
    return ProductRead.model_validate(product)


@product_router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    product_id: uuid.UUID,
    service: Annotated[ProductService, Depends(get_product_service)],
) -> Response:
    if not await service.delete_product(product_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found.")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
