import uuid

from catalog_service.category.model import Category
from catalog_service.category.repository import CategoryRepository
from catalog_service.category.schemas import CategoryCreate, CategoryUpdate


class CategoryAlreadyExistsError(Exception):
    """Raised when a category name is already in use."""


class CategoryService:
    def __init__(self, category_repository: CategoryRepository):
        self.category_repository = category_repository

    async def get_category_by_id(self, category_id: uuid.UUID) -> Category | None:
        return await self.category_repository.get_category_by_id(category_id)

    async def create_category(self, payload: CategoryCreate) -> Category:
        if await self.category_repository.get_category_by_name(payload.name):
            raise CategoryAlreadyExistsError

        category = Category(name=payload.name, description=payload.description)
        return await self.category_repository.create_category(category)

    async def update_category(
        self,
        category_id: uuid.UUID,
        payload: CategoryUpdate,
    ) -> Category | None:
        category = await self.category_repository.get_category_by_id(category_id)
        if category is None:
            return None

        updates = payload.model_dump(exclude_unset=True)
        if "name" in updates and updates["name"] != category.name:
            if await self.category_repository.get_category_by_name(updates["name"]):
                raise CategoryAlreadyExistsError

        for field, value in updates.items():
            setattr(category, field, value)
        return await self.category_repository.update_category(category)

    async def delete_category(self, category_id: uuid.UUID) -> bool:
        category = await self.category_repository.get_category_by_id(category_id)
        if category is None:
            return False
        await self.category_repository.delete_category(category)
        return True

    async def list_categories(self, *, limit: int, offset: int) -> list[Category]:
        return await self.category_repository.list_categories(limit=limit, offset=offset)
