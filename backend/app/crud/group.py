from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from app.models.group import Group
from app.crud.catalog_crud import CatalogCRUD

_crud = CatalogCRUD(Group, table_name="groups", search_fields=("name","code"))

async def create_group(db: AsyncSession, data: dict, user_id: UUID): return await _crud.create(db, data, user_id)
async def get_groups(db: AsyncSession, skip=0, limit=100, search=None, active=None, user_id: UUID | None = None): return await _crud.list(db, skip, limit, search, active, user_id)
async def get_group_by_id(db: AsyncSession, group_id: UUID): return await _crud.get_by_id(db, group_id)
async def update_group(db: AsyncSession, group_id: UUID, data: dict, user_id: UUID): return await _crud.update(db, group_id, data, user_id)
async def patch_group(db: AsyncSession, group_id: UUID, data: dict, user_id: UUID): return await _crud.patch(db, group_id, data, user_id)
async def delete_group(db: AsyncSession, group_id: UUID, user_id: UUID): return await _crud.delete(db, group_id, user_id)
