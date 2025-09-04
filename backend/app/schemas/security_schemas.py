# app/schemas/security_schemas.py
from pydantic import BaseModel, Field, field_validator
from typing import Optional, Any
import re

# Nota: mantenemos SecurityUtils como estaba
from app.utils.security_utils import SecurityUtils

CODE_REGEX = re.compile(r"^[A-Z0-9_-]+$")

class SecureBaseModel(BaseModel):
    """Sanitiza strings y estructuras anidadas en todos los modelos."""
    @field_validator('*', mode='before')
    @classmethod
    def _sanitize_all(cls, value: Any, info):
        field_name = info.field_name
        if isinstance(value, str):
            return SecurityUtils.sanitize_input(value, field_name)
        if isinstance(value, dict):
            return SecurityUtils.sanitize_data(value)
        if isinstance(value, list):
            out = []
            for item in value:
                if isinstance(item, dict):
                    out.append(SecurityUtils.sanitize_data(item))
                elif isinstance(item, str):
                    out.append(SecurityUtils.sanitize_input(item, field_name))
                else:
                    out.append(item)
            return out
        return value

    class Config:
        arbitrary_types_allowed = True
        validate_assignment = True


class EntityBase(SecureBaseModel):
    """
    Base reutilizable para catálogos con (code, name, description, active).
    Aplica mismos límites que PaymentTerm.
    """
    code: str = Field(..., min_length=1, max_length=SecurityUtils.FIELD_MAX_LENGTHS.get("code", 10))
    name: str = Field(..., min_length=1, max_length=SecurityUtils.FIELD_MAX_LENGTHS.get("name", 100))
    description: Optional[str] = Field(None, max_length=SecurityUtils.FIELD_MAX_LENGTHS.get("description", 500))
    active: bool = True

    @field_validator("code")
    @classmethod
    def _validate_code(cls, v: str) -> str:
        if not CODE_REGEX.match(v):
            raise ValueError("El código solo puede contener A-Z, 0-9, guion y guion_bajo")
        return v.upper()
