from pydantic import BaseModel
from uuid import UUID
from typing import Optional, List
from datetime import datetime

# BASE
class SubGroupBase(BaseModel):
    code: str
    name: str
    description: Optional[str] = None
    group_id: UUID  # Relación obligatoria con grupo

# CREATE (POST)
class SubGroupCreate(SubGroupBase):
    pass

# UPDATE (PUT)
class SubGroupUpdate(SubGroupBase):
    active: bool

# PATCH (parcial)
class SubGroupPatch(BaseModel):
    code: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    group_id: Optional[UUID] = None
    active: Optional[bool] = None

# LECTURA (GET)
class SubGroupRead(SubGroupBase):
    id: UUID
    code: str
    name: str
    group_name: str
    description: Optional[str] = None
    active: bool
    group_id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# RESPUESTA PAGINADA
class SubGroupListResponse(BaseModel):
    total: int
    items: List[SubGroupRead]

    class Config:
        from_attributes = True

# RESULTADO DE IMPORTACIÓN MASIVA
class SubGroupImportResult(BaseModel):
    total_imported: int
    total_errors: int
    imported: list
    errors: list
