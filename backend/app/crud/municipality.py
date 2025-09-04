# municipality.py
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from app.models.municipality import Municipality
from app.crud.catalog_crud import CatalogCRUD
_crud = CatalogCRUD(Municipality, table_name="municipalities", search_fields=("name","code"))
async def create_municipality(db: AsyncSession, data: dict, user_id: UUID): return await _crud.create(db, data, user_id)
async def get_municipalities(db: AsyncSession, skip=0, limit=100, search=None, active=None, user_id: UUID | None = None): return await _crud.list(db, skip, limit, search, active, user_id)
async def get_municipality_by_id(db: AsyncSession, municipality_id: UUID): return await _crud.get_by_id(db, municipality_id)
async def update_municipality(db: AsyncSession, municipality_id: UUID, data: dict, user_id: UUID): return await _crud.update(db, municipality_id, data, user_id)
async def patch_municipality(db: AsyncSession, municipality_id: UUID, data: dict, user_id: UUID): return await _crud.patch(db, municipality_id, data, user_id)
async def delete_municipality(db: AsyncSession, municipality_id: UUID, user_id: UUID): return await _crud.delete(db, municipality_id, user_id)