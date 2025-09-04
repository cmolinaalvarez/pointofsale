from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from app.models.subcategory import SubCategory
from app.crud.catalog_crud import CatalogCRUD

_crud = CatalogCRUD(SubCategory, table_name="subcategories", search_fields=("name","code"))

async def create_subcategory(db: AsyncSession, data: dict, user_id: UUID): return await _crud.create(db, data, user_id)
async def get_subcategories(db: AsyncSession, skip=0, limit=100, search=None, active=None, user_id: UUID | None = None): return await _crud.list(db, skip, limit, search, active, user_id)
async def get_subcategory_by_id(db: AsyncSession, subcategory_id: UUID): return await _crud.get_by_id(db, subcategory_id)
async def update_subcategory(db: AsyncSession, subcategory_id: UUID, data: dict, user_id: UUID): return await _crud.update(db, subcategory_id, data, user_id)
async def patch_subcategory(db: AsyncSession, subcategory_id: UUID, data: dict, user_id: UUID): return await _crud.patch(db, subcategory_id, data, user_id)
async def delete_subcategory(db: AsyncSession, subcategory_id: UUID, user_id: UUID): return await _crud.delete(db, subcategory_id, user_id)
