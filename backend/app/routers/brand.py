from fastapi import APIRouter
from app.routers.catalog_router import build_catalog_router
from app.crud.brand import _crud as brand_crud
from app.schemas.brand import BrandCreate, BrandUpdate, BrandRead, BrandPatch, BrandListResponse, BrandImportResult

router: APIRouter = build_catalog_router(
    prefix="/brands",
    tags=["Brands"],
    crud=brand_crud,
    SCreate=BrandCreate, SUpdate=BrandUpdate, SRead=BrandRead, SPatch=BrandPatch, SListResponse=BrandListResponse, SImportResult=BrandImportResult,
)
