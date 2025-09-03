from pydantic import BaseModel
from uuid import UUID
from typing import Optional, List
from datetime import datetime

# BASE
class CountryBase(BaseModel):
    code: str    
    name: str
    country_code: Optional[str] = None


# CREATE (POST)
class CountryCreate(CountryBase):
    pass

# UPDATE (PUT)
class CountryUpdate(CountryBase):
    active:bool

# PATCH (parcial)
class CountryPatch(BaseModel):
    code: Optional[str] = None
    name: Optional[str] = None
    country_code: Optional[str] = None
    active: Optional[bool] = None

# LECTURA (GET)
class CountryRead(CountryBase):
    id: UUID
    active: bool
    user_id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# LISTADO PAGINADO
class CountryListResponse(BaseModel):
    total: int
    items: List[CountryRead]

    class Config:
        from_attributes = True

# RESULTADO DE IMPORTACIÓN MASIVA
class CountryImportResult(BaseModel):
    total_imported: int
    total_errors: int
    imported: list
    errors: list
