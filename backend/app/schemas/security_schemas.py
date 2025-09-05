# app/schemas/security_schemas.py
from __future__ import annotations

from typing import Any, ClassVar, Dict, List, Optional
from pydantic import BaseModel, Field, ConfigDict, field_validator

# -------------------------------
# Constantes y regex reutilizables
# -------------------------------
CODE_MAX: int = 10
NAME_MAX: int = 100
DESC_MAX: int = 500

# Regex seguro para "code": MAYÚSCULAS, números, guion y guion bajo
CODE_RX: str = r"^[A-Z0-9_-]+$"

__all__ = [
    "SecureBaseModel",
    "EntityBase",
    "ImportResult",
    "CODE_RX",
    "CODE_MAX",
    "NAME_MAX",
    "DESC_MAX",
    "_sanitize",
]

# -------------------------------
# Sanitizador básico (usado por middleware)
# -------------------------------
def _sanitize(value: Any) -> Any:
    """
    Limpieza mínima y validaciones rápidas:
    - str: strip y control simple contra caracteres no imprimibles.
    - dict/list: recursivo.
    Lanza ValueError si detecta payload evidentemente malicioso.
    """
    if value is None:
        return None

    if isinstance(value, str):
        v = value.strip()
        # Bloquear NUL u otros controles peligrosos
        if any(ord(c) < 32 and c not in ("\t", "\n", "\r") for c in v):
            raise ValueError("Control characters not allowed")
        # Evitar cadenas con ángulos que puedan ser HTML peligroso en campos libres
        # (La validación fuerte va en schemas/middleware)
        return v

    if isinstance(value, list):
        return [_sanitize(x) for x in value]

    if isinstance(value, dict):
        return {k: _sanitize(v) for k, v in value.items()}

    return value

# -------------------------------
# Base segura para todos los schemas
# -------------------------------
class SecureBaseModel(BaseModel):
    """BaseModel con config común para todos los esquemas."""
    model_config = ConfigDict(from_attributes=True)

# -------------------------------
# Base de catálogos (code, name, description, active)
# -------------------------------
class EntityBase(SecureBaseModel):
    # límites reutilizables (no son campos Pydantic)
    CODE_MAX: ClassVar[int] = CODE_MAX
    NAME_MAX: ClassVar[int] = NAME_MAX
    DESC_MAX: ClassVar[int] = DESC_MAX

    code: str = Field(..., min_length=1, max_length=CODE_MAX, pattern=CODE_RX)
    name: str = Field(..., min_length=1, max_length=NAME_MAX)
    description: Optional[str] = Field(None, max_length=DESC_MAX)
    active: bool = Field(True)

    @field_validator("code")
    @classmethod
    def _code_upper_and_format(cls, v: str) -> str:
        vv = v.strip().upper()
        return vv

    @field_validator("name")
    @classmethod
    def _name_strip(cls, v: str) -> str:
        return v.strip()

    @field_validator("description")
    @classmethod
    def _desc_strip(cls, v: Optional[str]) -> Optional[str]:
        return None if v is None else v.strip()

# -------------------------------
# Resultado genérico de importación
# -------------------------------
class ImportResult(SecureBaseModel):
    total_imported: int
    total_errors: int
    imported: List[Any]
    errors: List[Dict[str, Any]]
