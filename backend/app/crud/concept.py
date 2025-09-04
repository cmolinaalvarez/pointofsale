from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from app.models.concept import Concept
from app.crud.catalog_crud import CatalogCRUD

_crud = CatalogCRUD(Concept, table_name="concepts", search_fields=("name","code"))

async def create_concept(db: AsyncSession, data: dict, user_id: UUID): return await _crud.create(db, data, user_id)
async def get_concepts(db: AsyncSession, skip=0, limit=100, search=None, active=None, user_id: UUID | None = None): return await _crud.list(db, skip, limit, search, active, user_id)
async def get_concept_by_id(db: AsyncSession, concept_id: UUID): return await _crud.get_by_id(db, concept_id)
async def update_concept(db: AsyncSession, concept_id: UUID, data: dict, user_id: UUID): return await _crud.update(db, concept_id, data, user_id)
async def patch_concept(db: AsyncSession, concept_id: UUID, data: dict, user_id: UUID): return await _crud.patch(db, concept_id, data, user_id)
async def delete_concept(db: AsyncSession, concept_id: UUID, user_id: UUID): return await _crud.delete(db, concept_id, user_id)
