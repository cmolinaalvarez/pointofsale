from typing import Optional, List
from uuid import UUID
from datetime import datetime
from pydantic import EmailStr, Field
from app.schemas.security_schemas import SecureBaseModel

class UserBase(SecureBaseModel):
    email: EmailStr
    full_name: Optional[str] = Field(None, max_length=100)
    active: bool = True

class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=128)

class UserUpdate(UserBase): pass

class UserPatch(SecureBaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, max_length=100)
    active: Optional[bool] = None
    password: Optional[str] = Field(None, min_length=8, max_length=128)

class UserRead(SecureBaseModel):
    id: UUID
    email: EmailStr
    full_name: Optional[str] = None
    active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    class Config: from_attributes = True

class UserListResponse(SecureBaseModel):
    total: int
    items: List[UserRead]
    class Config: from_attributes = True
