# division.py
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from app.models.division import Division
from app.crud.catalog_crud import CatalogCRUD
_crud = CatalogCRUD(Division, table_name="divisions", search_fields=("name","code"))
async def create_division(db: AsyncSession, data: dict, user_id: UUID): return await _crud.create(db, data, user_id)
async def get_divisions(db: AsyncSession, skip=0, limit=100, search=None, active=None, user_id: UUID | None = None): return await _crud.list(db, skip, limit, search, active, user_id)
async def get_division_by_id(db: AsyncSession, division_id: UUID): return await _crud.get_by_id(db, division_id)
async def update_division(db: AsyncSession, division_id: UUID, data: dict, user_id: UUID): return await _crud.update(db, division_id, data, user_id)
async def patch_division(db: AsyncSession, division_id: UUID, data: dict, user_id: UUID): return await _crud.patch(db, division_id, data, user_id)
async def delete_division(db: AsyncSession, division_id: UUID, user_id: UUID): return await _crud.delete(db, division_id, user_id)
