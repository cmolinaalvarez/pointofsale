# country.py
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from app.models.country import Country
from app.crud.catalog_crud import CatalogCRUD
_crud = CatalogCRUD(Country, table_name="countries", search_fields=("name","code"))
async def create_country(db: AsyncSession, data: dict, user_id: UUID): return await _crud.create(db, data, user_id)
async def get_countries(db: AsyncSession, skip=0, limit=100, search=None, active=None, user_id: UUID | None = None): return await _crud.list(db, skip, limit, search, active, user_id)
async def get_country_by_id(db: AsyncSession, country_id: UUID): return await _crud.get_by_id(db, country_id)
async def update_country(db: AsyncSession, country_id: UUID, data: dict, user_id: UUID): return await _crud.update(db, country_id, data, user_id)
async def patch_country(db: AsyncSession, country_id: UUID, data: dict, user_id: UUID): return await _crud.patch(db, country_id, data, user_id)
async def delete_country(db: AsyncSession, country_id: UUID, user_id: UUID): return await _crud.delete(db, country_id, user_id)
