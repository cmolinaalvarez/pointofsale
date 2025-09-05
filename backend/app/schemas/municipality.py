# app/schemas/municipality.py
from __future__ import annotations

from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime
from pydantic import Field, ConfigDict

from app.schemas.security_schemas import (
    EntityBase,      # code, name, description, active + validaciones comunes
    SecureBaseModel,
    CODE_RX,         # regex seguro para "code"
)

# ---------- Base ----------
class MunicipalityBase(EntityBase):
    pass

# ---------- Entrada ----------
class MunicipalityCreate(MunicipalityBase):
    pass

class MunicipalityUpdate(MunicipalityBase):
    pass

class MunicipalityPatch(SecureBaseModel):
    code: Optional[str] = Field(
        None, min_length=1, max_length=EntityBase.CODE_MAX, pattern=CODE_RX
    )
    name: Optional[str] = Field(None, min_length=1, max_length=EntityBase.NAME_MAX)
    description: Optional[str] = Field(None, max_length=EntityBase.DESC_MAX)
    active: Optional[bool] = None

# ---------- Salida ----------
class MunicipalityRead(SecureBaseModel):
    id: UUID
    code: str
    name: str
    description: Optional[str] = None
    active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    user_id: Optional[UUID] = None

    model_config = ConfigDict(from_attributes=True)

class MunicipalityListResponse(SecureBaseModel):
    total: int
    items: List[MunicipalityRead]

    model_config = ConfigDict(from_attributes=True)

# ---------- Resultado importación ----------
class MunicipalityImportResult(SecureBaseModel):
    total_imported: int
    total_errors: int
    imported: List[str]
    errors: List[Dict[str, Any]]
