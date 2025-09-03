from pydantic import BaseModel
from uuid import UUID
from typing import Optional, List
from datetime import datetime

# BASE
class MunicipalityBase(BaseModel):
    code: str
    name: str
    division_id: UUID
    division_code: str
  

# CREATE (POST)
class MunicipalityCreate(MunicipalityBase):
    division_id: UUID
    division_code: Optional[str] = None

# UPDATE (PUT)
class MunicipalityUpdate(MunicipalityBase):
     division_code: Optional[str] = None
     active: bool 

# PATCH (parcial)
class MunicipalityPatch(BaseModel):
    code: Optional[str] = None
    name: Optional[str] = None
    division_code: Optional[str] = None
    active: Optional[bool] = None

# LECTURA (GET)
class MunicipalityRead(MunicipalityBase):
    id: UUID
    code: str
    name: str
    division_id: UUID
    division_code: Optional[str] = None
    division_name: str
    active: bool
    user_id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# LISTADO PAGINADO
class MunicipalityListResponse(BaseModel):
    total: int
    items: List[MunicipalityRead]

    class Config:
        from_attributes = True

# RESULTADO DE IMPORTACIÓN MASIVA
class MunicipalityImportResult(BaseModel):
    total_imported: int
    total_errors: int
    imported: list
    errors: list
