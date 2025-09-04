# app/routers/document.py
from fastapi import APIRouter
from app.routers.catalog_router import build_catalog_router
from app.crud.document import _crud as document_crud
from app.schemas.document import DocumentCreate, DocumentUpdate, DocumentRead, DocumentPatch, DocumentListResponse, DocumentImportResult

router: APIRouter = build_catalog_router(
    prefix="/documents",
    tags=["Documents"],
    crud=document_crud,
    SCreate=DocumentCreate, SUpdate=DocumentUpdate, SRead=DocumentRead, SPatch=DocumentPatch, SListResponse=DocumentListResponse, SImportResult=DocumentImportResult,
)
