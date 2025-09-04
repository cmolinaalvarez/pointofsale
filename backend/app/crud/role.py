from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from app.models.role import Role
from app.crud.catalog_crud import CatalogCRUD

_crud = CatalogCRUD(Role, table_name="roles", search_fields=("name","code"))

async def create_role(db: AsyncSession, data: dict, user_id: UUID): return await _crud.create(db, data, user_id)
async def get_roles(db: AsyncSession, skip=0, limit=100, search=None, active=None, user_id: UUID | None = None): return await _crud.list(db, skip, limit, search, active, user_id)
async def get_role_by_id(db: AsyncSession, role_id: UUID): return await _crud.get_by_id(db, role_id)
async def update_role(db: AsyncSession, role_id: UUID, data: dict, user_id: UUID): return await _crud.update(db, role_id, data, user_id)
async def patch_role(db: AsyncSession, role_id: UUID, data: dict, user_id: UUID): return await _crud.patch(db, role_id, data, user_id)
async def delete_role(db: AsyncSession, role_id: UUID, user_id: UUID): return await _crud.delete(db, role_id, user_id)
