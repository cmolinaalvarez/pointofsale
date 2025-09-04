# app/routers/subgroup.py
from fastapi import APIRouter
from app.routers.catalog_router import build_catalog_router
from app.crud.subgroup import _crud as subgroup_crud
from app.schemas.subgroup import SubGroupCreate, SubGroupUpdate, SubGroupRead, SubGroupPatch, SubGroupListResponse, SubGroupImportResult

router: APIRouter = build_catalog_router(
    prefix="/subgroups",
    tags=["SubGroups"],
    crud=subgroup_crud,
    SCreate=SubGroupCreate, SUpdate=SubGroupUpdate, SRead=SubGroupRead, SPatch=SubGroupPatch, SListResponse=SubGroupListResponse, SImportResult=SubGroupImportResult,
)
