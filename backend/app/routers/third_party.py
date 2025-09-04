# app/routers/third_party.py
from fastapi import APIRouter
from app.routers.catalog_router import build_catalog_router
from app.crud.third_party import _crud as third_party_crud
from app.schemas.third_party import ThirdPartyCreate, ThirdPartyUpdate, ThirdPartyRead, ThirdPartyPatch, ThirdPartyListResponse, ThirdPartyImportResult

router: APIRouter = build_catalog_router(
    prefix="/thirdparties",
    tags=["ThirdParties"],
    crud=third_party_crud,
    SCreate=ThirdPartyCreate, SUpdate=ThirdPartyUpdate, SRead=ThirdPartyRead, SPatch=ThirdPartyPatch, SListResponse=ThirdPartyListResponse, SImportResult=ThirdPartyImportResult,
)
