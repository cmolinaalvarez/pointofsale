# app/routers/setting.py
from fastapi import APIRouter
from app.routers.catalog_router import build_catalog_router
from app.crud.setting import _crud as setting_crud
from app.schemas.setting import SettingCreate, SettingUpdate, SettingRead, SettingPatch, SettingListResponse, SettingImportResult

router: APIRouter = build_catalog_router(
    prefix="/settings",
    tags=["Settings"],
    crud=setting_crud,
    SCreate=SettingCreate, SUpdate=SettingUpdate, SRead=SettingRead, SPatch=SettingPatch, SListResponse=SettingListResponse, SImportResult=SettingImportResult,
)
