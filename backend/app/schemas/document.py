# app/schemas/document.py
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
class DocumentBase(EntityBase):
    # Si tu modelo Document tiene campos extra (p.ej. serie, prefix, etc.) agrégalos aquí:
    # series: Optional[str] = Field(None, max_length=20)
    pass

# ---------- Entrada ----------
class DocumentCreate(DocumentBase):
    pass

class DocumentUpdate(DocumentBase):
    pass

class DocumentPatch(SecureBaseModel):
    code: Optional[str] = Field(
        None, min_length=1, max_length=EntityBase.CODE_MAX, pattern=CODE_RX
    )
    name: Optional[str] = Field(None, min_length=1, max_length=EntityBase.NAME_MAX)
    description: Optional[str] = Field(None, max_length=EntityBase.DESC_MAX)
    active: Optional[bool] = None
    # series: Optional[str] = Field(None, max_length=20)  # si aplica

# ---------- Salida ----------
class DocumentRead(SecureBaseModel):
    id: UUID
    code: str
    name: str
    description: Optional[str] = None
    active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    user_id: Optional[UUID] = None

    model_config = ConfigDict(from_attributes=True)

class DocumentListResponse(SecureBaseModel):
    total: int
    items: List[DocumentRead]

    model_config = ConfigDict(from_attributes=True)

# ---------- Resultado importación ----------
class DocumentImportResult(SecureBaseModel):
    total_imported: int
    total_errors: int
    imported: List[str]
    errors: List[Dict[str, Any]]
