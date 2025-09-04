# app/routers/product.py
from fastapi import APIRouter
from app.routers.catalog_router import build_catalog_router
from app.crud.product import _crud as product_crud
from app.schemas.product import ProductCreate, ProductUpdate, ProductRead, ProductPatch, ProductListResponse, ProductImportResult

router: APIRouter = build_catalog_router(
    prefix="/products",
    tags=["Products"],
    crud=product_crud,
    SCreate=ProductCreate, SUpdate=ProductUpdate, SRead=ProductRead, SPatch=ProductPatch, SListResponse=ProductListResponse, SImportResult=ProductImportResult,
)
