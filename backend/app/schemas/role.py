# app/schemas/role.py
from __future__ import annotations

import json
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime
from pydantic import Field, ConfigDict, field_validator

from app.schemas.security_schemas import (
    EntityBase,       # code, name, description, active + validaciones comunes
    SecureBaseModel,
    CODE_RX,
)

# =============================
# Base
# =============================
class RoleBase(EntityBase):
    role_type: Optional[str] = Field(
        default="USER",
        description="Tipo lógico del rol (p.ej. ADMIN, USER)",
        pattern=r"^[A-Z_]{3,32}$",
    )
    scopes: Optional[List[str]] = Field(
        default=None,
        description="Lista de scopes permitidos para este rol",
    )
    is_admin: bool = Field(default=False, description="Indicador si el rol es de administrador")

    # Aceptar scopes como string (JSON o separado por coma/espacios) o lista
    @field_validator("scopes", mode="before")
    @classmethod
    def _coerce_scopes(cls, v):
        if v is None or v == "":
            return None
        if isinstance(v, list):
            return [str(s).strip() for s in v if str(s).strip()]
        if isinstance(v, str):
            s = v.strip()
            # si viene como JSON '["read","write"]'
            if (s.startswith("[") and s.endswith("]")) or (s.startswith('"') and s.endswith('"')):
                try:
                    parsed = json.loads(s)
                    if isinstance(parsed, list):
                        return [str(x).strip() for x in parsed if str(x).strip()]
                    if isinstance(parsed, str):
                        s = parsed
                except Exception:
                    pass
            # admitir "read write" o "read,write"
            if "," in s:
                return [p.strip() for p in s.split(",") if p.strip()]
            return [p.strip() for p in s.split() if p.strip()]
        # cualquier otro tipo -> convertir a string
        return [str(v).strip()]

# =============================
# Entrada
# =============================
class RoleCreate(RoleBase):
    pass

class RoleUpdate(RoleBase):
    pass

class RolePatch(SecureBaseModel):
    code: Optional[str] = Field(None, min_length=1, max_length=EntityBase.CODE_MAX, pattern=CODE_RX)
    name: Optional[str] = Field(None, min_length=1, max_length=EntityBase.NAME_MAX)
    description: Optional[str] = Field(None, max_length=EntityBase.DESC_MAX)
    active: Optional[bool] = None
    role_type: Optional[str] = Field(default=None, pattern=r"^[A-Z_]{3,32}$")
    scopes: Optional[List[str]] = None
    is_admin: Optional[bool] = None

    # mismo coercion que en Base
    @field_validator("scopes", mode="before")
    @classmethod
    def _coerce_scopes_patch(cls, v):
        return RoleBase._coerce_scopes(v)

# =============================
# Salida
# =============================
class RoleRead(SecureBaseModel):
    id: UUID
    code: str
    name: str
    description: Optional[str] = None
    active: bool
    role_type: Optional[str] = None
    scopes: Optional[List[str]] = None
    is_admin: bool = False
    created_at: datetime
    updated_at: Optional[datetime] = None
    user_id: Optional[UUID] = None

    model_config = ConfigDict(from_attributes=True, extra="ignore")

class RoleListResponse(SecureBaseModel):
    total: int
    items: List[RoleRead]
    model_config = ConfigDict(from_attributes=True)

# =============================
# Resultado de importación
# =============================
class RoleImportResult(SecureBaseModel):
    total_imported: int
    total_errors: int
    imported: List[str]
    errors: List[Dict[str, Any]]
