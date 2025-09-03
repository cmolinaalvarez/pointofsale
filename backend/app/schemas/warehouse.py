from pydantic import BaseModel
from uuid import UUID
from typing import Optional, List
from datetime import datetime

# BASE
class WarehouseBase(BaseModel):
    code: str
    name: str
    description: Optional[str] = None
    location: Optional[str] = None
    active: bool = True

# CREATE (POST)
class WarehouseCreate(WarehouseBase):
    pass

# UPDATE (PUT)
class WarehouseUpdate(WarehouseBase):
    pass

# PATCH (parcial)
class WarehousePatch(BaseModel):
    code: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None
    active: Optional[bool] = None

# LECTURA (GET)
class WarehouseRead(WarehouseBase):
    id: UUID
    code: str
    name: str
    description: Optional[str] = None
    location: Optional[str] = None
    active: bool
    user_id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# LISTADO PAGINADO
class WarehouseListResponse(BaseModel):
    total: int
    items: List[WarehouseRead]

    class Config:
        from_attributes = True

# RESULTADO DE IMPORTACIÓN MASIVA
class WarehouseImportResult(BaseModel):
    total_imported: int
    total_errors: int
    imported: list
    errors: list
