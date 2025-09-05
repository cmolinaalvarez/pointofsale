# app/schemas/third_party.py
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
class ThirdPartyBase(EntityBase):
    # Si luego agregas más campos propios del tercero, decláralos aquí.
    pass

# ---------- Entrada ----------
class ThirdPartyCreate(ThirdPartyBase):
    pass

class ThirdPartyUpdate(ThirdPartyBase):
    pass

class ThirdPartyPatch(SecureBaseModel):
    code: Optional[str] = Field(None, min_length=1, max_length=EntityBase.CODE_MAX, pattern=CODE_RX)
    name: Optional[str] = Field(None, min_length=1, max_length=EntityBase.NAME_MAX)
    description: Optional[str] = Field(None, max_length=EntityBase.DESC_MAX)
    active: Optional[bool] = None

# ---------- Salida ----------
class ThirdPartyRead(SecureBaseModel):
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

class ThirdPartyListResponse(SecureBaseModel):
    total: int
    items: List[ThirdPartyRead]

    model_config = ConfigDict(from_attributes=True)


# Al final de app/schemas/third_party.py
from app.schemas.security_schemas import ImportResult as _GenericImportResult

class ThirdPartyImportResult(_GenericImportResult): 
    pass

