from pydantic import BaseModel
from uuid import UUID
from typing import Optional, List
from datetime import datetime

# BASE
class DivisionBase(BaseModel):
    code: str
    name: str
    country_id: UUID
   
# CREATE (POST)
class DivisionCreate(DivisionBase):
    country_code: Optional[str] = None
    iso_3166_2: Optional[str] = None

# UPDATE (PUT)
class DivisionUpdate(DivisionBase):
    country_code: Optional[str] = None
    iso_3166_2: Optional[str] = None
    active: bool 

# PATCH (parcial)
class DivisionPatch(BaseModel):
    code: Optional[str] = None
    name: Optional[str] = None
    country_id: Optional[UUID] = None
    country_code: Optional[str] = None
    iso_3166_2: Optional[str] = None
    active: Optional[bool] = None

# LECTURA (GET)
class DivisionRead(DivisionBase):
    id: UUID
    code: str
    name: str
    country_id: UUID
    country_code: Optional[str] = None
    iso_3166_2: Optional[str] = None
    country_name: str
    active: bool
    user_id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# LISTADO PAGINADO
class DivisionListResponse(BaseModel):
    total: int
    items: List[DivisionRead]

    class Config:
        from_attributes = True

# RESULTADO DE IMPORTACIÓN MASIVA
class DivisionImportResult(BaseModel):
    total_imported: int
    total_errors: int
    imported: list
    errors: list
