# app/routers/payment_term.py
from fastapi import APIRouter
from app.routers.catalog_router import build_catalog_router
from app.crud.payment_term import _crud as payment_term_crud
from app.schemas.payment_term import (
    PaymentTermCreate, PaymentTermUpdate, PaymentTermRead, PaymentTermPatch,
    PaymentTermListResponse, PaymentTermImportResult
)

router: APIRouter = build_catalog_router(
    prefix="/paymentterms",  
    tags=["PaymentTerms"],
    crud=payment_term_crud,
    SCreate=PaymentTermCreate, SUpdate=PaymentTermUpdate, SRead=PaymentTermRead, SPatch=PaymentTermPatch, SListResponse=PaymentTermListResponse, SImportResult=PaymentTermImportResult,
)
