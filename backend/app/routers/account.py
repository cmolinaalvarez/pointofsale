# app/routers/account.py
from fastapi import APIRouter
from app.routers.catalog_router import build_catalog_router
from app.crud.account import _crud as account_crud
from app.schemas.account import AccountCreate, AccountUpdate, AccountRead, AccountPatch, AccountListResponse, AccountImportResult

router: APIRouter = build_catalog_router(
    prefix="/accounts",
    tags=["Accounts"],
    crud=account_crud,
    SCreate=AccountCreate, SUpdate=AccountUpdate, SRead=AccountRead, SPatch=AccountPatch, SListResponse=AccountListResponse, SImportResult=AccountImportResult,
)
