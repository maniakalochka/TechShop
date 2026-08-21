import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from catalog_service.category.model import Category


class CategoryRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_category_by_id(self, category_id: uuid.UUID) -> Category | None:
        return await self.session.get(Category, category_id)

    async def get_category_by_name(self, name: str) -> Category | None:
        result = await self.session.execute(select(Category).where(Category.name == name))
        return result.scalar_one_or_none()

    async def create_category(self, category: Category) -> Category:
        self.session.add(category)
        await self.session.commit()
        await self.session.refresh(category)
        return category

    async def update_category(self, category: Category) -> Category:
        await self.session.commit()
        await self.session.refresh(category)
        return category

    async def delete_category(self, category: Category) -> None:
        await self.session.delete(category)
        await self.session.commit()

    async def list_categories(self, *, limit: int, offset: int) -> list[Category]:
        stmt = select(Category).order_by(Category.name).limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
