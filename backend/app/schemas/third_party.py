# app/schemas/third_party.py
from pydantic import BaseModel, EmailStr
from uuid import UUID
from typing import Optional, List
from datetime import datetime
from enum import Enum


# ==============================
# ENUMS
# ==============================
class ThirdPartyTypeEnum(str, Enum):
    C = "C"  # Cliente
    P = "P"  # Proveedor
    A = "A"  # Ambos


class PersonTypeEnum(str, Enum):
    N = "N"  # Natural
    J = "J"  # Jurídica
    A = "A"  # Ambos


# ==============================
# BASE
# ==============================
class ThirdPartyBase(BaseModel):
    name: str
    third_party_type: ThirdPartyTypeEnum
    person_type: PersonTypeEnum

    contact_name: Optional[str] = None
    phone: Optional[str] = None
    cell_phone: Optional[str] = None
    email: Optional[EmailStr] = None
    address: Optional[str] = None

    municipality_id: Optional[UUID] = None
    division_id: Optional[UUID] = None
    country_id: Optional[UUID] = None

    nit: Optional[str] = None
    active: bool = True


# ==============================
# CREATE (POST)
# ==============================
class ThirdPartyCreate(ThirdPartyBase):
    pass


# ==============================
# UPDATE (PUT)
# ==============================
class ThirdPartyUpdate(ThirdPartyBase):
    active: bool  # explícito para asegurar consistencia


# ==============================
# PATCH (parcial)
# ==============================
class ThirdPartyPatch(BaseModel):
    name: Optional[str] = None
    third_party_type: Optional[ThirdPartyTypeEnum] = None
    person_type: Optional[PersonTypeEnum] = None

    contact_name: Optional[str] = None
    phone: Optional[str] = None
    cell_phone: Optional[str] = None
    email: Optional[EmailStr] = None
    address: Optional[str] = None

    municipality_id: Optional[UUID] = None
    division_id: Optional[UUID] = None
    country_id: Optional[UUID] = None

    nit: Optional[str] = None
    active: Optional[bool] = None


# ==============================
# LECTURA (GET)
# ==============================
class ThirdPartyRead(ThirdPartyBase):
    id: UUID
    user_id: UUID
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ==============================
# LISTADO PAGINADO
# ==============================
class ThirdPartyListResponse(BaseModel):
    total: int
    items: List[ThirdPartyRead]

    class Config:
        from_attributes = True


# ==============================
# RESULTADO DE IMPORTACIÓN MASIVA
# ==============================
class ThirdPartyImportResult(BaseModel):
    total_imported: int
    total_errors: int
    imported: list
    errors: list
