# app/schemas/user.py
from typing import Optional, List
from uuid import UUID
from datetime import datetime
from pydantic import EmailStr, Field, ConfigDict, computed_field
from app.schemas.security_schemas import SecureBaseModel

class UserBase(SecureBaseModel):
    email: EmailStr
    full_name: Optional[str] = Field(None, max_length=100)
    active: bool = True

class UserCreate(UserBase):
    username: str = Field(..., min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_.-]+$")
    password: str = Field(..., min_length=8, max_length=128)

class UserUpdate(UserBase):
    username: str = Field(..., min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_.-]+$")

class UserPatch(SecureBaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = Field(None, min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_.-]+$")
    full_name: Optional[str] = Field(None, max_length=100)
    active: Optional[bool] = None
    password: Optional[str] = Field(None, min_length=8, max_length=128)

class UserRead(SecureBaseModel):
    id: UUID
    email: EmailStr
    username: str
    full_name: Optional[str] = None
    active: bool
    superuser: bool = Field(default=False, exclude=True)  # solo para calcular role
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

    @computed_field(return_type=str)
    def role(self) -> str:
        return "admin" if getattr(self, "superuser", False) else "user"

class UserListResponse(SecureBaseModel):
    total: int
    items: List[UserRead]

    model_config = ConfigDict(from_attributes=True)
