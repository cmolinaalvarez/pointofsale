from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from app.models.subgroup import SubGroup
from app.crud.catalog_crud import CatalogCRUD

_crud = CatalogCRUD(SubGroup, table_name="subgroups", search_fields=("name","code"))

async def create_subgroup(db: AsyncSession, data: dict, user_id: UUID): return await _crud.create(db, data, user_id)
async def get_subgroups(db: AsyncSession, skip=0, limit=100, search=None, active=None, user_id: UUID | None = None): return await _crud.list(db, skip, limit, search, active, user_id)
async def get_subgroup_by_id(db: AsyncSession, subgroup_id: UUID): return await _crud.get_by_id(db, subgroup_id)
async def update_subgroup(db: AsyncSession, subgroup_id: UUID, data: dict, user_id: UUID): return await _crud.update(db, subgroup_id, data, user_id)
async def patch_subgroup(db: AsyncSession, subgroup_id: UUID, data: dict, user_id: UUID): return await _crud.patch(db, subgroup_id, data, user_id)
async def delete_subgroup(db: AsyncSession, subgroup_id: UUID, user_id: UUID): return await _crud.delete(db, subgroup_id, user_id)
