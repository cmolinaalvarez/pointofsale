from pydantic import BaseModel
from uuid import UUID
from typing import Optional, List
from datetime import datetime

# BASE
class GroupBase(BaseModel):
    code: str
    name: str
    description: Optional[str] = None
    subcategory_id: UUID

# CREATE (POST)
class GroupCreate(GroupBase):
    pass

# UPDATE (PUT)
class GroupUpdate(GroupBase):
    active: bool

# PATCH (PARCIAL)
class GroupPatch(BaseModel):
    code: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    subcategory_id: Optional[UUID] = None
    active: Optional[bool] = None    

# LECTURA (GET)
class GroupRead(GroupBase):
    id: UUID
    code: str
    name: str
    subcategory_name: str
    description: Optional[str] = None
    active: bool
    subcategory_id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# RESPUESTA PAGINADA
class GroupListResponse(BaseModel):
    total: int
    items: List[GroupRead]

    class Config:
        from_attributes = True

# RESULTADO DE IMPORTACIÓN MASIVA
class GroupImportResult(BaseModel):
    total_imported: int
    total_errors: int
    imported: list
    errors: list
