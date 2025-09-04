# app/routers/warehouse.py
from fastapi import APIRouter
from app.routers.catalog_router import build_catalog_router
from app.crud.warehouse import _crud as warehouse_crud
from app.schemas.warehouse import WarehouseCreate, WarehouseUpdate, WarehouseRead, WarehousePatch, WarehouseListResponse, WarehouseImportResult

router: APIRouter = build_catalog_router(
    prefix="/warehouses",
    tags=["Warehouses"],
    crud=warehouse_crud,
    SCreate=WarehouseCreate, SUpdate=WarehouseUpdate, SRead=WarehouseRead, SPatch=WarehousePatch, SListResponse=WarehouseListResponse, SImportResult=WarehouseImportResult,
)
