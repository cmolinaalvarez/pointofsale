from typing import Optional, List
from uuid import UUID
from datetime import datetime
from app.schemas.security_schemas import SecureBaseModel

class PurchaseBase(SecureBaseModel):
    model_config = {"extra": "allow"}

class PurchaseCreate(PurchaseBase): pass
class PurchaseUpdate(PurchaseBase): pass

class PurchasePatch(SecureBaseModel):
    model_config = {"extra": "allow"}

class PurchaseRead(SecureBaseModel):
    id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None
    user_id: UUID
    model_config = {"from_attributes": True, "extra": "allow"}

class PurchaseListResponse(SecureBaseModel):
    total: int
    items: List[PurchaseRead]
    class Config: from_attributes = True
