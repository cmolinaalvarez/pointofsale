from pydantic import Field, EmailStr
from uuid import UUID
from typing import Optional, List
from datetime import datetime
from app.schemas.security_schemas import EntityBase, SecureBaseModel

class ThirdPartyBase(EntityBase):
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=32)

class ThirdPartyCreate(ThirdPartyBase): pass
class ThirdPartyUpdate(ThirdPartyBase): pass

class ThirdPartyPatch(SecureBaseModel):
    code: Optional[str] = Field(None, min_length=1, max_length=10)
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    active: Optional[bool] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=32)

class ThirdPartyRead(SecureBaseModel):
    id: UUID
    code: str
    name: str
    description: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    user_id: UUID
    class Config: from_attributes = True

class ThirdPartyListResponse(SecureBaseModel):
    total: int
    items: List[ThirdPartyRead]
    class Config: from_attributes = True
    
class ThirdPartyImportResult(SecureBaseModel):
    total_imported: int
    total_errors: int
    imported: list
    errors: list
