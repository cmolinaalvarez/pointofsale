from pydantic import BaseModel
from uuid import UUID
from typing import Optional, List, Dict
from datetime import datetime

class ConceptBase(BaseModel):
    code: str
    name: str
    description: Optional[str] = None
    concept_type: str
    debit_account_id: UUID
    credit_account_id: UUID    
    active: bool = True

class ConceptCreate(ConceptBase):
    pass

class ConceptUpdate(ConceptBase):
    pass

class ConceptPatch(BaseModel):
    code: Optional[str] = None
    name: Optional[str] = None    
    description: Optional[str] = None
    concept_type: Optional[str] = None
    debit_account_id: Optional[UUID] = None
    credit_account_id: Optional[UUID] = None   
    active: Optional[bool] = None

class ConceptRead(ConceptBase):
    id: UUID
    user_id: UUID
    debit_account_name: Optional[str] = None  # ✅ Nuevo campo
    credit_account_name: Optional[str] = None  # ✅ Nuevo campo
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class ConceptImportResult(BaseModel):
    total_imported: int
    total_errors: int
    imported: list
    errors: list