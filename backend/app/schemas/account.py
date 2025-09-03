# app/schemas/account.py

from pydantic import BaseModel, Field
from uuid import UUID
from typing import Optional, List
from datetime import datetime

# ====================================================
# BASE (común para crear/actualizar)
# ====================================================

class AccountBase(BaseModel):
    code:str
    name: str = Field(..., max_length=100, description="Nombre de la cuenta contable")
    description: Optional[str] = Field(None, max_length=255, description="Descripción de la cuenta")
    account_type: str = Field(..., max_length=20, description="Tipo de cuenta (ej: 'activo', 'pasivo', etc.)")
    active: bool = Field(default=True, description="Indica si la cuenta está activa")

# ====================================================
# CREACIÓN (POST)
# ====================================================

class AccountCreate(AccountBase):
    pass

# ====================================================
# ACTUALIZACIÓN COMPLETA (PUT)
# ====================================================

class AccountUpdate(AccountBase):
    pass

# ====================================================
# ACTUALIZACIÓN PARCIAL (PATCH)
# ====================================================

class AccountPatch(BaseModel):
    code: Optional[str] = Field(None, max_length=20)
    name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = Field(None, max_length=255)
    account_type: Optional[str] = Field(None, max_length=20)
    active: Optional[bool]

# ====================================================
# LECTURA (GET)
# ====================================================

class AccountRead(AccountBase):
    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# ====================================================
# RESPUESTA PAGINADA
# ====================================================

class AccountListResponse(BaseModel):
    total: int
    items: List[AccountRead]

    class Config:
        from_attributes = True

# ====================================================
# RESULTADO DE IMPORTACIÓN MASIVA
# ====================================================

class AccountImportResult(BaseModel):
    total_imported: int
    total_errors: int
    imported: list
    errors: list
