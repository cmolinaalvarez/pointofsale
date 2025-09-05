from __future__ import annotations
from typing import Optional, List
from uuid import UUID
from datetime import datetime
from pydantic import Field, ConfigDict, field_validator
from app.schemas.security_schemas import EntityBase, SecureBaseModel, ImportResult as _GenericImportResult

# Nota: nombres usados en router: SubCategory*
class SubCategoryBase(EntityBase): pass
class SubCategoryCreate(SubCategoryBase): pass
class SubCategoryUpdate(SubCategoryBase): pass

class SubCategoryPatch(SecureBaseModel):
    code: Optional[str] = Field(None, min_length=1, max_length=EntityBase.CODE_MAX)
    name: Optional[str] = Field(None, min_length=1, max_length=EntityBase.NAME_MAX)
    description: Optional[str] = Field(None, max_length=EntityBase.DESC_MAX)
    active: Optional[bool] = None

    @field_validator("code")
    @classmethod
    def _code_format(cls, v: str) -> str:
        return EntityBase._code_format(v)

class SubCategoryRead(SecureBaseModel):
    id: UUID
    code: str
    name: str
    description: Optional[str] = None
    active: bool
    user_id: Optional[UUID] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)

class SubCategoryListResponse(SecureBaseModel):
    total: int
    items: List[SubCategoryRead]
    model_config = ConfigDict(from_attributes=True)

class SubCategoryImportResult(_GenericImportResult): pass
