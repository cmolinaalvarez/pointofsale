from pydantic import BaseModel
from uuid import UUID
from typing import Optional, List
from datetime import datetime

# =====================
# BASE
# =====================
class SettingBase(BaseModel):
    key: str
    value: Optional[str] = None
    type: str = "string"
    description: Optional[str] = None

# =====================
# CREATE (POST)
# =====================
class SettingCreate(SettingBase):
    key: str
    value: Optional[str] = None
    type: str = "string"
    description: Optional[str] = None

# =====================
# UPDATE (PUT)
# =====================
class SettingUpdate(SettingBase):
    active: bool

# =====================
# PATCH (PATCH)
# =====================
class SettingPatch(BaseModel):
    key: Optional[str] = None
    value: Optional[str] = None
    type: Optional[str] = None
    description: Optional[str] = None
    user_id: Optional[UUID] = None
    active: Optional[bool] = None

# =====================
# LECTURA (GET)
# =====================
class SettingRead(SettingBase):
    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None
    active:bool

    class Config:
        from_attributes = True

# =====================
# RESPUESTA DE LISTA
# =====================
class SettingListResponse(BaseModel):
    total: int
    items: List[SettingRead]

    class Config:
        from_attributes = True

# =====================
# RESULTADO DE IMPORTACIÓN MASIVA (opcional)
# =====================
class SettingImportResult(BaseModel):
    total_imported: int
    total_errors: int
    imported: list
    errors: list
