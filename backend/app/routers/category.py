# app/routers/category.py
from fastapi import APIRouter
from app.routers.catalog_router import build_catalog_router
from app.crud.category import _crud as category_crud
from app.schemas.category import CategoryCreate, CategoryUpdate, CategoryRead, CategoryPatch, CategoryListResponse, CategoryImportResult

router: APIRouter = build_catalog_router(
    prefix="/categories",
    tags=["Categories"],
    crud=category_crud,
    SCreate=CategoryCreate, SUpdate=CategoryUpdate, SRead=CategoryRead, SPatch=CategoryPatch, SListResponse=CategoryListResponse, SImportResult=CategoryImportResult,
)
