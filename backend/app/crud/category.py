from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from app.models.category import Category
from app.crud.catalog_crud import CatalogCRUD

_crud = CatalogCRUD(Category, table_name="categories", search_fields=("name","code"))

async def create_category(db: AsyncSession, data: dict, user_id: UUID): return await _crud.create(db, data, user_id)
async def get_categories(db: AsyncSession, skip=0, limit=100, search=None, active=None, user_id: UUID | None = None): return await _crud.list(db, skip, limit, search, active, user_id)
async def get_category_by_id(db: AsyncSession, category_id: UUID): return await _crud.get_by_id(db, category_id)
async def update_category(db: AsyncSession, category_id: UUID, data: dict, user_id: UUID): return await _crud.update(db, category_id, data, user_id)
async def patch_category(db: AsyncSession, category_id: UUID, data: dict, user_id: UUID): return await _crud.patch(db, category_id, data, user_id)
async def delete_category(db: AsyncSession, category_id: UUID, user_id: UUID): return await _crud.delete(db, category_id, user_id)
