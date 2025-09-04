# app/routers/municipality.py
from fastapi import APIRouter
from app.routers.catalog_router import build_catalog_router
from app.crud.municipality import _crud as municipality_crud
from app.schemas.municipality import MunicipalityCreate, MunicipalityUpdate, MunicipalityRead, MunicipalityPatch, MunicipalityListResponse, MunicipalityImportResult

router: APIRouter = build_catalog_router(
    prefix="/municipalities",
    tags=["Municipalities"],
    crud=municipality_crud,
    SCreate=MunicipalityCreate, SUpdate=MunicipalityUpdate, SRead=MunicipalityRead, SPatch=MunicipalityPatch, SListResponse=MunicipalityListResponse, SImportResult=MunicipalityImportResult,
)
