# app/routers/group.py
from fastapi import APIRouter
from app.routers.catalog_router import build_catalog_router
from app.crud.group import _crud as group_crud
from app.schemas.group import GroupCreate, GroupUpdate, GroupRead, GroupPatch, GroupListResponse, GroupImportResult

router: APIRouter = build_catalog_router(
    prefix="/groups",
    tags=["Groups"],
    crud=group_crud,
    SCreate=GroupCreate, SUpdate=GroupUpdate, SRead=GroupRead, SPatch=GroupPatch, SListResponse=GroupListResponse, SImportResult=GroupImportResult,
)
