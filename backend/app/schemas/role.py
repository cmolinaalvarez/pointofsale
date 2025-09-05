from __future__ import annotations
from typing import Optional, List
from uuid import UUID
from datetime import datetime
from pydantic import Field, ConfigDict, field_validator, model_validator
from app.schemas.security_schemas import EntityBase, SecureBaseModel, ImportResult as _GenericImportResult

class RoleBase(EntityBase):
    role_type: Optional[str] = Field(None, min_length=1, max_length=20, description="Tipo de rol (ej. USER, ADMIN)")
    scopes: List[str] = Field(default_factory=list, description="Scopes permitidos")
    is_admin: bool = Field(default=False, description="Marca si es administrador")

class RoleCreate(RoleBase): pass
class RoleUpdate(RoleBase): pass

class RolePatch(SecureBaseModel):
    code: Optional[str] = Field(None, min_length=1, max_length=EntityBase.CODE_MAX)
    name: Optional[str] = Field(None, min_length=1, max_length=EntityBase.NAME_MAX)
    description: Optional[str] = Field(None, max_length=EntityBase.DESC_MAX)
    active: Optional[bool] = None
    role_type: Optional[str] = Field(None, min_length=1, max_length=20)
    scopes: Optional[List[str]] = None
    is_admin: Optional[bool] = None

    @field_validator("code")
    @classmethod
    def _code_format(cls, v: str) -> str:
        return EntityBase._code_format(v)

    @field_validator("scopes")
    @classmethod
    def _scopes_norm(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        if v is None: return v
        cleaned = []
        for s in v:
            s = (s or "").strip().lower()
            if not s: continue
            cleaned.append(s)
        return sorted(set(cleaned))

class RoleRead(SecureBaseModel):
    id: UUID
    code: str
    name: str
    description: Optional[str] = None
    active: bool
    role_type: Optional[str] = None
    scopes: List[str] = []
    is_admin: bool = False
    user_id: Optional[UUID] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)

class RoleListResponse(SecureBaseModel):
    total: int
    items: List[RoleRead]
    model_config = ConfigDict(from_attributes=True)

class RoleImportResult(_GenericImportResult): pass
