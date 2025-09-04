# app/routers/country.py
from fastapi import APIRouter
from app.routers.catalog_router import build_catalog_router
from app.crud.country import _crud as country_crud
from app.schemas.country import CountryCreate, CountryUpdate, CountryRead, CountryPatch, CountryListResponse, CountryImportResult

router: APIRouter = build_catalog_router(
    prefix="/countries",
    tags=["Countries"],
    crud=country_crud,
    SCreate=CountryCreate, SUpdate=CountryUpdate, SRead=CountryRead, SPatch=CountryPatch, SListResponse=CountryListResponse, SImportResult=CountryImportResult,
)
