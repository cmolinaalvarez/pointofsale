from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from app.models.product import Product
from app.crud.catalog_crud import CatalogCRUD

# Incluye sku en búsqueda si existe
_crud = CatalogCRUD(Product, table_name="products", search_fields=("name","code","sku"))

async def create_product(db: AsyncSession, data: dict, user_id: UUID): return await _crud.create(db, data, user_id)
async def get_products(db: AsyncSession, skip=0, limit=100, search=None, active=None, user_id: UUID | None = None): return await _crud.list(db, skip, limit, search, active, user_id)
async def get_product_by_id(db: AsyncSession, product_id: UUID): return await _crud.get_by_id(db, product_id)
async def update_product(db: AsyncSession, product_id: UUID, data: dict, user_id: UUID): return await _crud.update(db, product_id, data, user_id)
async def patch_product(db: AsyncSession, product_id: UUID, data: dict, user_id: UUID): return await _crud.patch(db, product_id, data, user_id)
async def delete_product(db: AsyncSession, product_id: UUID, user_id: UUID): return await _crud.delete(db, product_id, user_id)
