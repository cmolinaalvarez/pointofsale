from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from app.models.brand import Brand
from app.crud.catalog_crud import CatalogCRUD

_crud = CatalogCRUD(Brand, table_name="brands", search_fields=("name","code"))

async def create_brand(db: AsyncSession, data: dict, user_id: UUID): return await _crud.create(db, data, user_id)
async def get_brands(db: AsyncSession, skip=0, limit=100, search=None, active=None, user_id: UUID | None = None): return await _crud.list(db, skip, limit, search, active, user_id)
async def get_brand_by_id(db: AsyncSession, brand_id: UUID): return await _crud.get_by_id(db, brand_id)
async def update_brand(db: AsyncSession, brand_id: UUID, data: dict, user_id: UUID): return await _crud.update(db, brand_id, data, user_id)
async def patch_brand(db: AsyncSession, brand_id: UUID, data: dict, user_id: UUID): return await _crud.patch(db, brand_id, data, user_id)
async def delete_brand(db: AsyncSession, brand_id: UUID, user_id: UUID): return await _crud.delete(db, brand_id, user_id)
