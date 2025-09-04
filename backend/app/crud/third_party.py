from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from app.models.third_party import ThirdParty
from app.crud.catalog_crud import CatalogCRUD

_crud = CatalogCRUD(ThirdParty, table_name="third_parties", search_fields=("name","code"))

async def create_third_party(db: AsyncSession, data: dict, user_id: UUID): return await _crud.create(db, data, user_id)
async def get_third_parties(db: AsyncSession, skip=0, limit=100, search=None, active=None, user_id: UUID | None = None): return await _crud.list(db, skip, limit, search, active, user_id)
async def get_third_party_by_id(db: AsyncSession, third_party_id: UUID): return await _crud.get_by_id(db, third_party_id)
async def update_third_party(db: AsyncSession, third_party_id: UUID, data: dict, user_id: UUID): return await _crud.update(db, third_party_id, data, user_id)
async def patch_third_party(db: AsyncSession, third_party_id: UUID, data: dict, user_id: UUID): return await _crud.patch(db, third_party_id, data, user_id)
async def delete_third_party(db: AsyncSession, third_party_id: UUID, user_id: UUID): return await _crud.delete(db, third_party_id, user_id)
