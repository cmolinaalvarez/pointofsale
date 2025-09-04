from typing import Optional, List, Any
from uuid import UUID
from datetime import datetime
from pydantic import Field
from app.schemas.security_schemas import SecureBaseModel

class SettingBase(SecureBaseModel):
    key: str = Field(..., min_length=1, max_length=64)
    value: Any = None
    description: Optional[str] = Field(None, max_length=500)
    active: bool = True

class SettingCreate(SettingBase): pass
class SettingUpdate(SettingBase): pass

class SettingPatch(SecureBaseModel):
    key: Optional[str] = Field(None, min_length=1, max_length=64)
    value: Optional[Any] = None
    description: Optional[str] = Field(None, max_length=500)
    active: Optional[bool] = None

class SettingRead(SecureBaseModel):
    id: UUID
    key: str
    value: Any
    description: Optional[str] = None
    active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    user_id: UUID
    class Config: from_attributes = True

class SettingListResponse(SecureBaseModel):
    total: int
    items: List[SettingRead]
    class Config: from_attributes = True
