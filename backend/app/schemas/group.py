from pydantic import Field
from uuid import UUID
from typing import Optional, List
from datetime import datetime
from app.schemas.security_schemas import EntityBase, SecureBaseModel

class GroupBase(EntityBase): pass
class GroupCreate(GroupBase): pass
class GroupUpdate(GroupBase): pass

class GroupPatch(SecureBaseModel):
    code: Optional[str] = Field(None, min_length=1, max_length=10)
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    active: Optional[bool] = None

class GroupRead(SecureBaseModel):
    id: UUID
    code: str
    name: str
    description: Optional[str] = None
    active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    user_id: UUID
    class Config: from_attributes = True

class GroupListResponse(SecureBaseModel):
    total: int
    items: List[GroupRead]
    class Config: from_attributes = True

class GroupImportResult(SecureBaseModel):
    total_imported: int
    total_errors: int
    imported: list
    errors: list
