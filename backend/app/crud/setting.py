from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from app.models.setting import Setting
from app.crud.catalog_crud import CatalogCRUD

# Unicidad por "key" en lugar de "code"
_crud = CatalogCRUD(Setting, table_name="settings", unique_fields=("key",), search_fields=("key","description"), order_field="key", active_field="active")

async def create_setting(db: AsyncSession, data: dict, user_id: UUID): return await _crud.create(db, data, user_id)
async def get_settings(db: AsyncSession, skip=0, limit=100, search=None, active=None, user_id: UUID | None = None): return await _crud.list(db, skip, limit, search, active, user_id)
async def get_setting_by_id(db: AsyncSession, setting_id: UUID): return await _crud.get_by_id(db, setting_id)
async def update_setting(db: AsyncSession, setting_id: UUID, data: dict, user_id: UUID): return await _crud.update(db, setting_id, data, user_id)
async def patch_setting(db: AsyncSession, setting_id: UUID, data: dict, user_id: UUID): return await _crud.patch(db, setting_id, data, user_id)
async def delete_setting(db: AsyncSession, setting_id: UUID, user_id: UUID): return await _crud.delete(db, setting_id, user_id)
