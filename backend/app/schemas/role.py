from pydantic import Field
from uuid import UUID
from typing import Optional, List, Dict, Any
from datetime import datetime
from app.schemas.security_schemas import EntityBase, SecureBaseModel

class RoleBase(EntityBase):
    permissions: Optional[Dict[str, Any]] = None

class RoleCreate(RoleBase): pass
class RoleUpdate(RoleBase): pass

class RolePatch(SecureBaseModel):
    code: Optional[str] = Field(None, min_length=1, max_length=10)
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    permissions: Optional[Dict[str, Any]] = None
    active: Optional[bool] = None

class RoleRead(SecureBaseModel):
    id: UUID
    code: str
    name: str
    description: Optional[str] = None
    permissions: Optional[Dict[str, Any]] = None
    active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    user_id: UUID
    class Config: from_attributes = True

class RoleListResponse(SecureBaseModel):
    total: int
    items: List[RoleRead]
    class Config: from_attributes = True
    
class RoleImportResult(SecureBaseModel):
    total_imported: int
    total_errors: int
    imported: list
    errors: list
