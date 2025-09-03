from typing import Optional, List
from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from app.models.role import RoleType

class RoleBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    description: Optional[str] = None
    role_type: Optional[RoleType] = RoleType.VIEWER
    scopes: Optional[List[str]] = None   # era str
    is_admin: bool = False
    active: bool = True

class RoleCreate(RoleBase):
    pass

class RoleUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    description: Optional[str] = None
    role_type: Optional[RoleType] = None
    scopes: Optional[List[str]] = None
    is_admin: Optional[bool] = None
    active: Optional[bool] = None

class RolePatch(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    description: Optional[str] = None
    scopes: Optional[List[str]] = None
    active: Optional[bool] = None

class RoleRead(RoleBase):
    id: UUID
    created_at: datetime
    updated_at: Optional[datetime]
    user_id:UUID

    class Config:
        from_attributes = True

class RoleListResponse(BaseModel):
    total: int
    items: List[RoleRead]