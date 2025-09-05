# app/schemas/warehouse.py
from __future__ import annotations

from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime
from pydantic import Field, ConfigDict

from app.schemas.security_schemas import (
    EntityBase,       # code, name, description, active + validaciones comunes
    SecureBaseModel,
    CODE_RX,          # regex seguro para "code"
)

# ---------- Base ----------
class WarehouseBase(EntityBase):
    # Si luego agregas más campos del modelo, decláralos aquí (opcionales)
    pass

# ---------- Entrada ----------
class WarehouseCreate(WarehouseBase):
    pass

class WarehouseUpdate(WarehouseBase):
    pass

class WarehousePatch(SecureBaseModel):
    code: Optional[str] = Field(None, min_length=1, max_length=EntityBase.CODE_MAX, pattern=CODE_RX)
    name: Optional[str] = Field(None, min_length=1, max_length=EntityBase.NAME_MAX)
    description: Optional[str] = Field(None, max_length=EntityBase.DESC_MAX)
    active: Optional[bool] = None

# ---------- Salida ----------
class WarehouseRead(SecureBaseModel):
    id: UUID
    code: str
    name: str
    description: Optional[str] = None
    active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    user_id: Optional[UUID] = None

    # Ignora columnas/props extra del ORM
    model_config = ConfigDict(from_attributes=True, extra="ignore")

class WarehouseListResponse(SecureBaseModel):
    total: int
    items: List[WarehouseRead]

    model_config = ConfigDict(from_attributes=True)

# ---------- Resultado importación ----------
class WarehouseImportResult(SecureBaseModel):
    total_imported: int
    total_errors: int
    imported: List[str]
    errors: List[Dict[str, Any]]
