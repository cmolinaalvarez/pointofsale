# app/routers/division.py
from fastapi import APIRouter
from app.routers.catalog_router import build_catalog_router
from app.crud.division import _crud as division_crud
from app.schemas.division import DivisionCreate, DivisionUpdate, DivisionRead, DivisionPatch, DivisionListResponse, DivisionImportResult

router: APIRouter = build_catalog_router(
    prefix="/divisions",
    tags=["Divisions"],
    crud=division_crud,
    SCreate=DivisionCreate, SUpdate=DivisionUpdate, SRead=DivisionRead, SPatch=DivisionPatch, SListResponse=DivisionListResponse, SImportResult=DivisionImportResult,
)
