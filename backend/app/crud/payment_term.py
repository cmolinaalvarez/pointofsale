# app/crud/payment_terms.py
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from app.models.payment_term import PaymentTerm
from app.crud.catalog_crud import CatalogCRUD

_crud = CatalogCRUD(
    PaymentTerm,
    table_name="payment_terms",
    search_fields=("name", "code"),
)

async def create_payment_term(db: AsyncSession, data: dict, user_id: UUID):
    return await _crud.create(db, data, user_id)

async def get_payment_terms(db: AsyncSession, skip=0, limit=100, search=None, active=None, user_id: UUID | None = None):
    return await _crud.list(db, skip, limit, search, active, user_id)

async def get_payment_term_by_id(db: AsyncSession, payment_term_id: UUID):
    return await _crud.get_by_id(db, payment_term_id)

async def update_payment_term(db: AsyncSession, payment_term_id: UUID, data: dict, user_id: UUID):
    return await _crud.update(db, payment_term_id, data, user_id)

async def patch_payment_term(db: AsyncSession, payment_term_id: UUID, data: dict, user_id: UUID):
    return await _crud.patch(db, payment_term_id, data, user_id)

async def delete_payment_term(db: AsyncSession, payment_term_id: UUID, user_id: UUID):
    return await _crud.delete(db, payment_term_id, user_id)
