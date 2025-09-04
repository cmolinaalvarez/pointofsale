from typing import Optional, List
from uuid import UUID
from datetime import datetime
from app.schemas.security_schemas import SecureBaseModel

class StockBase(SecureBaseModel):
    model_config = {"extra": "allow"}

class StockCreate(StockBase): pass
class StockUpdate(StockBase): pass

class StockPatch(SecureBaseModel):
    model_config = {"extra": "allow"}

class StockRead(SecureBaseModel):
    id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None
    user_id: UUID
    model_config = {"from_attributes": True, "extra": "allow"}

class StockListResponse(SecureBaseModel):
    total: int
    items: List[StockRead]
    class Config: from_attributes = True
