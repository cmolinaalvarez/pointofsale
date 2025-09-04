# document.py
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from app.models.document import Document
from app.crud.catalog_crud import CatalogCRUD
_crud = CatalogCRUD(Document, table_name="documents", search_fields=("name","code"))
async def create_document(db: AsyncSession, data: dict, user_id: UUID): return await _crud.create(db, data, user_id)
async def get_documents(db: AsyncSession, skip=0, limit=100, search=None, active=None, user_id: UUID | None = None): return await _crud.list(db, skip, limit, search, active, user_id)
async def get_document_by_id(db: AsyncSession, document_id: UUID): return await _crud.get_by_id(db, document_id)
async def update_document(db: AsyncSession, document_id: UUID, data: dict, user_id: UUID): return await _crud.update(db, document_id, data, user_id)
async def patch_document(db: AsyncSession, document_id: UUID, data: dict, user_id: UUID): return await _crud.patch(db, document_id, data, user_id)
async def delete_document(db: AsyncSession, document_id: UUID, user_id: UUID): return await _crud.delete(db, document_id, user_id)
