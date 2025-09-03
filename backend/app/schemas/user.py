from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field
from uuid import UUID
from datetime import datetime

# Importar el enum de roles del modelo
from app.models.role import RoleType

# ======================
# SCHEMAS Pydantic User
# ======================

# Schema básico para Role
class RoleRead(BaseModel):
    id: UUID
    name: str
    role_type: str
    is_admin: bool
    
    class Config:
        from_attributes = True

class UserBase(BaseModel):
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    full_name : Optional[str] = Field(None, min_length=6)
    superuser: Optional[bool] = None
    
class UserCreate(UserBase):  
    email: EmailStr = Field(..., example="usuario@dominio.com")  
    password: str = Field(..., min_length=6, example="12345678")
    role_id: Optional[UUID] = Field(None, description="ID del rol asignado")

class UserUpdate(UserBase):
    password: Optional[str] = Field(None, min_length=6, example="nueva_contraseña")
    active: bool
    superuser: bool
    role_id: Optional[UUID] = None

class UserPatch(BaseModel): 
    email: Optional[EmailStr] = None
    password: Optional[str] = Field(None, min_length=6)
    active: Optional[bool] = None
    superuser: Optional[bool] = None
    role_id: Optional[UUID] = None

class UserRead(UserBase):
    id: UUID
    full_name : Optional[str]
    email: EmailStr
    active: bool
    superuser: bool
    role_id: Optional[UUID]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True

# Para listados (paginación, igual que BrandListResponse)
class UserListResponse(BaseModel):
    total: int
    items: List[UserRead]
