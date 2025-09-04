# app/routers/concept.py
from fastapi import APIRouter
from app.routers.catalog_router import build_catalog_router
from app.crud.concept import _crud as concept_crud
from app.schemas.concept import ConceptCreate, ConceptUpdate, ConceptRead, ConceptPatch, ConceptListResponse, ConceptImportResult

router: APIRouter = build_catalog_router(
    prefix="/concepts",
    tags=["Concepts"],
    crud=concept_crud,
    SCreate=ConceptCreate, SUpdate=ConceptUpdate, SRead=ConceptRead, SPatch=ConceptPatch, SListResponse=ConceptListResponse, SImportResult=ConceptImportResult,
)
