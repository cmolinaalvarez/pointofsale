from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from app.models.unit import Unit
from app.crud.catalog_crud import CatalogCRUD

_crud = CatalogCRUD(Unit, table_name="units", search_fields=("name","code"))

async def create_unit(db: AsyncSession, data: dict, user_id: UUID): return await _crud.create(db, data, user_id)
async def get_units(db: AsyncSession, skip=0, limit=100, search=None, active=None, user_id: UUID | None = None): return await _crud.list(db, skip, limit, search, active, user_id)
async def get_unit_by_id(db: AsyncSession, unit_id: UUID): return await _crud.get_by_id(db, unit_id)
async def update_unit(db: AsyncSession, unit_id: UUID, data: dict, user_id: UUID): return await _crud.update(db, unit_id, data, user_id)
async def patch_unit(db: AsyncSession, unit_id: UUID, data: dict, user_id: UUID): return await _crud.patch(db, unit_id, data, user_id)
async def delete_unit(db: AsyncSession, unit_id: UUID, user_id: UUID): return await _crud.delete(db, unit_id, user_id)
