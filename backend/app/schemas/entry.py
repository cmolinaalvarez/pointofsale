from typing import Optional, List, Any, Dict
from uuid import UUID
from datetime import datetime
from pydantic import Field
from app.schemas.security_schemas import SecureBaseModel

class EntryBase(SecureBaseModel):
    # Acepta campos adicionales de tu modelo (líneas, totales, etc.)
    model_config = {"extra": "allow"}

class EntryCreate(EntryBase): pass
class EntryUpdate(EntryBase): pass

class EntryPatch(SecureBaseModel):
    model_config = {"extra": "allow"}  # permite parches parciales arbitrarios

class EntryRead(SecureBaseModel):
    id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None
    user_id: UUID
    model_config = {"from_attributes": True, "extra": "allow"}

class EntryListResponse(SecureBaseModel):
    total: int
    items: List[EntryRead]
    class Config: from_attributes = True
