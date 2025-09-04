# app/routers/role.py
from fastapi import APIRouter
from app.routers.catalog_router import build_catalog_router
from app.crud.role import _crud as role_crud
from app.schemas.role import RoleCreate, RoleUpdate, RoleRead, RolePatch, RoleListResponse, RoleImportResult

router: APIRouter = build_catalog_router(
    prefix="/roles",
    tags=["Roles"],
    crud=role_crud,
    SCreate=RoleCreate, SUpdate=RoleUpdate, SRead=RoleRead, SPatch=RolePatch, SListResponse=RoleListResponse, SImportResult=RoleImportResult,
)
