from pydantic import Field
from uuid import UUID
from typing import Optional, List
from datetime import datetime
from app.schemas.security_schemas import EntityBase, SecureBaseModel

class DocumentBase(EntityBase):
    uses_yearly_sequence: bool = True

class DocumentCreate(DocumentBase): pass
class DocumentUpdate(DocumentBase): pass

class DocumentPatch(SecureBaseModel):
    code: Optional[str] = Field(None, min_length=1, max_length=10)
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    uses_yearly_sequence: Optional[bool] = None
    active: Optional[bool] = None

class DocumentRead(SecureBaseModel):
    id: UUID
    code: str
    name: str
    description: Optional[str] = None
    uses_yearly_sequence: bool
    active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    user_id: UUID
    class Config: from_attributes = True

class DocumentListResponse(SecureBaseModel):
    total: int
    items: List[DocumentRead]
    class Config: from_attributes = True
    
class DocumentImportResult(SecureBaseModel):
    total_imported: int
    total_errors: int
    imported: list
    errors: list
