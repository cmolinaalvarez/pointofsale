from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from app.models.warehouse import Warehouse
from app.crud.catalog_crud import CatalogCRUD

_crud = CatalogCRUD(Warehouse, table_name="warehouses", search_fields=("name","code"))

async def create_warehouse(db: AsyncSession, data: dict, user_id: UUID): return await _crud.create(db, data, user_id)
async def get_warehouses(db: AsyncSession, skip=0, limit=100, search=None, active=None, user_id: UUID | None = None): return await _crud.list(db, skip, limit, search, active, user_id)
async def get_warehouse_by_id(db: AsyncSession, warehouse_id: UUID): return await _crud.get_by_id(db, warehouse_id)
async def update_warehouse(db: AsyncSession, warehouse_id: UUID, data: dict, user_id: UUID): return await _crud.update(db, warehouse_id, data, user_id)
async def patch_warehouse(db: AsyncSession, warehouse_id: UUID, data: dict, user_id: UUID): return await _crud.patch(db, warehouse_id, data, user_id)
async def delete_warehouse(db: AsyncSession, warehouse_id: UUID, user_id: UUID): return await _crud.delete(db, warehouse_id, user_id)
