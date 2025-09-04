from pydantic import Field
from uuid import UUID
from typing import Optional, List
from datetime import datetime
from enum import Enum
from app.schemas.security_schemas import EntityBase, SecureBaseModel

class AccountType(str, Enum):
    ASSET="ASSET"; LIABILITY="LIABILITY"; EQUITY="EQUITY"; INCOME="INCOME"; EXPENSE="EXPENSE"

class AccountBase(EntityBase):
    account_type: AccountType

class AccountCreate(AccountBase): pass
class AccountUpdate(AccountBase): pass

class AccountPatch(SecureBaseModel):
    code: Optional[str] = Field(None, min_length=1, max_length=10)
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    active: Optional[bool] = None
    account_type: Optional[AccountType] = None

class AccountRead(SecureBaseModel):
    id: UUID
    code: str
    name: str
    description: Optional[str] = None
    account_type: AccountType
    active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    user_id: UUID
    class Config: from_attributes = True

class AccountListResponse(SecureBaseModel):
    total: int
    items: List[AccountRead]
    class Config: from_attributes = True
