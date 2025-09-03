from pydantic import BaseModel
from uuid import UUID
from typing import Optional, List
from datetime import datetime

# BASE
class SubCategoryBase(BaseModel):
    code: str
    name: str  
    description: Optional[str] = None
    category_id: UUID  # Relación obligatoria con categoría

# CREATE (POST)
class SubCategoryCreate(SubCategoryBase):
    pass

# UPDATE (PUT)
class SubCategoryUpdate(SubCategoryBase):
    active: bool

# PATCH (parcial)
class SubCategoryPatch(BaseModel):
    code: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    category_id: Optional[UUID] = None
    active: Optional[bool] = None


# LECTURA (GET)
class SubCategoryRead(SubCategoryBase):
    id: UUID
    code: str
    name: str
    category_name: str
    description: Optional[str] = None
    active: bool
    category_id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# RESPUESTA PAGINADA
class SubCategoryListResponse(BaseModel):
    total: int
    items: List[SubCategoryRead]

    class Config:
        from_attributes = True

# RESULTADO DE IMPORTACIÓN MASIVA
class SubCategoryImportResult(BaseModel):
    total_imported: int
    total_errors: int
    imported: list
    errors: list
