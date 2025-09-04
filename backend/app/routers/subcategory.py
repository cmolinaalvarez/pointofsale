# app/routers/subcategory.py
from fastapi import APIRouter
from app.routers.catalog_router import build_catalog_router
from app.crud.subcategory import _crud as subcategory_crud
from app.schemas.subcategory import SubCategoryCreate, SubCategoryUpdate, SubCategoryRead, SubCategoryPatch, SubCategoryListResponse, SubCategoryImportResult

router: APIRouter = build_catalog_router(
    prefix="/subcategories",
    tags=["SubCategories"],
    crud=subcategory_crud,
    SCreate=SubCategoryCreate, SUpdate=SubCategoryUpdate, SRead=SubCategoryRead, SPatch=SubCategoryPatch, SListResponse=SubCategoryListResponse, SImportResult=SubCategoryImportResult,
)
