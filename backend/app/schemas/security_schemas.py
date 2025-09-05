# app/schemas/security_schemas.py
from __future__ import annotations
from typing import Optional, ClassVar, Dict
from pydantic import BaseModel, Field, ConfigDict, field_validator

class SecureBaseModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        validate_assignment=True,
        from_attributes=True,
    )

# Patrón seguro para "code": alfanumérico, puede incluir . _ -
CODE_RX = r"^[A-Za-z0-9][A-Za-z0-9._-]{0,9}$"

def _reject_control_chars(v: str) -> str:
    # Evita controles ASCII (mitiga payloads maliciosos)
    if any(ord(c) < 32 for c in v):
        raise ValueError("control characters not allowed")
    return v

class EntityBase(SecureBaseModel):
    # ---- Constantes (deben ser ClassVar en Pydantic v2) ----
    CODE_MAX: ClassVar[int] = 10
    NAME_MAX: ClassVar[int] = 100
    DESC_MAX: ClassVar[int] = 500
    FIELD_MAX_LENGTHS: ClassVar[Dict[str, int]] = {
        "code": CODE_MAX, "name": NAME_MAX, "description": DESC_MAX
    }

    # ---- Campos comunes de catálogo ----
    code: str = Field(..., min_length=1, max_length=CODE_MAX, pattern=CODE_RX)
    name: str = Field(..., min_length=1, max_length=NAME_MAX)
    description: Optional[str] = Field(default=None, max_length=DESC_MAX)
    active: bool = True

    # ---- Validaciones adicionales ----
    @field_validator("code")
    @classmethod
    def _v_code(cls, v: str) -> str:
        return _reject_control_chars(v)

    @field_validator("name", "description")
    @classmethod
    def _v_text(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        return _reject_control_chars(v)
