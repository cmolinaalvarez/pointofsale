from pydantic import BaseModel
from uuid import UUID
from typing import Optional, List
from datetime import datetime

# BASE
class CategoryBase(BaseModel):
    code: str
    name: str
    description: Optional[str] = None
    active: bool = True

# CREATE (POST)
class CategoryCreate(CategoryBase):
    pass

# UPDATE (PUT)
class CategoryUpdate(CategoryBase):
    pass

# PATCH (parcial)
class CategoryPatch(BaseModel):
    code: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    active: Optional[bool] = None

# LECTURA (GET)
class CategoryRead(CategoryBase):
    id: UUID
    code: str
    name: str
    description: Optional[str] = None
    active: bool
    user_id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# LISTADO PAGINADO
class CategoryListResponse(BaseModel):
    total: int
    items: List[CategoryRead]

    class Config:
        from_attributes = True

# RESULTADO DE IMPORTACIÓN MASIVA
class CategoryImportResult(BaseModel):
    total_imported: int
    total_errors: int
    imported: list
    errors: list
