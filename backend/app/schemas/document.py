from pydantic import BaseModel
from uuid import UUID
from typing import Optional, List
from datetime import datetime

# BASE
class DocumentBase(BaseModel):
    code: str
    name: str
    description: str
    prefix: str
    document_type: str
    

# CREATE (POST)
class DocumentCreate(DocumentBase):
    pass

# UPDATE (PUT)
class DocumentUpdate(DocumentBase):
    active: bool = True

# PATCH (parcial)
class DocumentPatch(BaseModel):
    code: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    prefix: Optional[str] = None
    document_type: Optional[str] = None
    active: Optional[bool] = None

# LECTURA (GET)
class DocumentRead(DocumentBase):
    id: UUID
    code: str
    name: str
    description: Optional[str] = None
    prefix: Optional[str] = None
    document_type: Optional[str] = None
    active: bool
    user_id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# LISTADO PAGINADO
class DocumentListResponse(BaseModel):
    total: int
    items: List[DocumentRead]

    class Config:
        from_attributes = True

# RESULTADO DE IMPORTACIÓN MASIVA
class DocumentImportResult(BaseModel):
    total_imported: int
    total_errors: int
    imported: list
    errors: list
