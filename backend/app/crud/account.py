from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from app.models.account import Account
from app.crud.catalog_crud import CatalogCRUD

_crud = CatalogCRUD(Account, table_name="accounts", search_fields=("name","code"))

async def create_account(db: AsyncSession, data: dict, user_id: UUID): return await _crud.create(db, data, user_id)
async def get_accounts(db: AsyncSession, skip=0, limit=100, search=None, active=None, user_id: UUID | None = None): return await _crud.list(db, skip, limit, search, active, user_id)
async def get_account_by_id(db: AsyncSession, account_id: UUID): return await _crud.get_by_id(db, account_id)
async def update_account(db: AsyncSession, account_id: UUID, data: dict, user_id: UUID): return await _crud.update(db, account_id, data, user_id)
async def patch_account(db: AsyncSession, account_id: UUID, data: dict, user_id: UUID): return await _crud.patch(db, account_id, data, user_id)
async def delete_account(db: AsyncSession, account_id: UUID, user_id: UUID): return await _crud.delete(db, account_id, user_id)
