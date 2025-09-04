from pydantic import Field
from uuid import UUID
from typing import Optional, List
from datetime import datetime
from app.schemas.security_schemas import EntityBase, SecureBaseModel

class MunicipalityBase(EntityBase): pass
class MunicipalityCreate(MunicipalityBase): pass
class MunicipalityUpdate(MunicipalityBase): pass

class MunicipalityPatch(SecureBaseModel):
    code: Optional[str] = Field(None, min_length=1, max_length=10)
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    active: Optional[bool] = None

class MunicipalityRead(SecureBaseModel):
    id: UUID
    code: str
    name: str
    description: Optional[str] = None
    active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    user_id: UUID
    division_id: Optional[UUID] = None
    class Config: from_attributes = True

class MunicipalityListResponse(SecureBaseModel):
    total: int
    items: List[MunicipalityRead]
    class Config: from_attributes = True
    

class MunicipalityImportResult(SecureBaseModel):
    total_imported: int
    total_errors: int
    imported: list
    errors: list
