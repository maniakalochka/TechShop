import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status

from catalog_service.category.dependencies import get_category_service
from catalog_service.category.schemas import CategoryCreate, CategoryRead, CategoryUpdate
from catalog_service.category.service import CategoryAlreadyExistsError, CategoryService

category_router = APIRouter(prefix="/categories", tags=["categories"])


@category_router.post("", response_model=CategoryRead, status_code=status.HTTP_201_CREATED)
async def create_category(
    payload: CategoryCreate,
    service: Annotated[CategoryService, Depends(get_category_service)],
) -> CategoryRead:
    try:
        category = await service.create_category(payload)
    except CategoryAlreadyExistsError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Category name already exists."
        ) from error
    return CategoryRead.model_validate(category)


@category_router.get("", response_model=list[CategoryRead])
async def list_categories(
    service: Annotated[CategoryService, Depends(get_category_service)],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[CategoryRead]:
    categories = await service.list_categories(limit=limit, offset=offset)
    return [CategoryRead.model_validate(category) for category in categories]


@category_router.get("/{category_id}", response_model=CategoryRead)
async def get_category(
    category_id: uuid.UUID,
    service: Annotated[CategoryService, Depends(get_category_service)],
) -> CategoryRead:
    category = await service.get_category_by_id(category_id)
    if category is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found.")
    return CategoryRead.model_validate(category)


@category_router.patch("/{category_id}", response_model=CategoryRead)
async def update_category(
    category_id: uuid.UUID,
    payload: CategoryUpdate,
    service: Annotated[CategoryService, Depends(get_category_service)],
) -> CategoryRead:
    try:
        category = await service.update_category(category_id, payload)
    except CategoryAlreadyExistsError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Category name already exists."
        ) from error
    if category is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found.")
    return CategoryRead.model_validate(category)


@category_router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(
    category_id: uuid.UUID,
    service: Annotated[CategoryService, Depends(get_category_service)],
) -> Response:
    if not await service.delete_category(category_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found.")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
