from pydantic import BaseModel
from uuid import UUID
from typing import Optional, List
from datetime import datetime

# BASE
class BrandBase(BaseModel):
    code: str
    name: str
    description: Optional[str] = None
    active: bool = True

# CREATE (POST)
class BrandCreate(BrandBase):
    pass
# UPDATE (PUT)
class BrandUpdate(BrandBase):
    pass  # Igual, si son los mismos campos que BrandBase

# PATCH (parcial)
class BrandPatch(BaseModel):
    code: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    active: Optional[bool] = None

# LECTURA (GET)
class BrandRead(BrandBase):
    id: UUID
    code: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    active: Optional[bool] = None
    user_id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# -- Este es el schema que te faltaba --
class BrandListResponse(BaseModel):
    total: int
    items: List[BrandRead]

    class Config:
        from_attributes = True
        


class BrandImportResult(BaseModel):
    total_imported: int
    total_errors: int
    imported: list
    errors: list

