# app/routers/unit.py
from fastapi import APIRouter
from app.routers.catalog_router import build_catalog_router
from app.crud.unit import _crud as unit_crud
from app.schemas.unit import UnitCreate, UnitUpdate, UnitRead, UnitPatch, UnitListResponse, UnitImportResult

router: APIRouter = build_catalog_router(
    prefix="/units",
    tags=["Units"],
    crud=unit_crud,
    SCreate=UnitCreate, SUpdate=UnitUpdate, SRead=UnitRead, SPatch=UnitPatch, SListResponse=UnitListResponse, SImportResult=UnitImportResult,
)
