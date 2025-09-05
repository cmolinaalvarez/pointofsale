# app/schemas/payment_term.py
from __future__ import annotations

import re
from uuid import UUID
from typing import Optional, List
from datetime import datetime

from pydantic import Field, ConfigDict, field_validator

from app.schemas.security_schemas import (
    SecureBaseModel,
    EntityBase,   # code, name, description, active + validaciones comunes
    CODE_RX,      # regex central para "code"
)

# Valores permitidos para la base de cálculo
BASIS_ALLOWED: tuple[str, ...] = ("Factura", "Recepción", "Entrega", "Fin de mes")


# =============================
# Base (entrada con validaciones)
# =============================
class PaymentTermBase(EntityBase):
    net_days: int = Field(..., ge=0, description="Días netos para pago")
    discount_percent: float = Field(
        ..., ge=0.0, le=100.0, description="Porcentaje de descuento por pronto pago"
    )
    discount_days: int = Field(..., ge=0, description="Días para aplicar descuento")
    basis: str = Field(..., min_length=1, max_length=20, description="Base de cálculo")

    # Normaliza/valida el code usando la expresión centralizada
    @field_validator("code", mode="before")
    @classmethod
    def _normalize_code(cls, v: str) -> str:
        if v is None:
            return v
        s = str(v).strip().upper()
        if not re.fullmatch(CODE_RX, s):
            raise ValueError("El código solo puede contener letras mayúsculas, números, guiones y guiones bajos")
        return s

    @field_validator("basis")
    @classmethod
    def _validate_basis(cls, v: str) -> str:
        if v not in BASIS_ALLOWED:
            raise ValueError(f'La base debe ser una de: {", ".join(BASIS_ALLOWED)}')
        return v


# =============================
# Create / Update
# =============================
class PaymentTermCreate(PaymentTermBase):
    pass


class PaymentTermUpdate(PaymentTermBase):
    pass


# =============================
# Patch (parcial)
# =============================
class PaymentTermPatch(SecureBaseModel):
    code: Optional[str] = Field(None, min_length=1, max_length=EntityBase.CODE_MAX, description="Código")
    name: Optional[str] = Field(None, min_length=1, max_length=EntityBase.NAME_MAX, description="Nombre")
    description: Optional[str] = Field(None, max_length=EntityBase.DESC_MAX, description="Descripción")
    active: Optional[bool] = Field(None, description="Activo")

    net_days: Optional[int] = Field(None, ge=0, description="Días netos para pago")
    discount_percent: Optional[float] = Field(None, ge=0.0, le=100.0, description="Porcentaje de descuento")
    discount_days: Optional[int] = Field(None, ge=0, description="Días para aplicar descuento")
    basis: Optional[str] = Field(None, min_length=1, max_length=20, description="Base de cálculo")

    @field_validator("code", mode="before")
    @classmethod
    def _normalize_code(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        s = str(v).strip().upper()
        if not re.fullmatch(CODE_RX, s):
            raise ValueError("El código solo puede contener letras mayúsculas, números, guiones y guiones bajos")
        return s

    @field_validator("basis")
    @classmethod
    def _validate_basis(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        if v not in BASIS_ALLOWED:
            raise ValueError(f'La base debe ser una de: {", ".join(BASIS_ALLOWED)}')
        return v


# =============================
# Read / List / Import
# =============================
class PaymentTermRead(PaymentTermBase):
    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class PaymentTermListResponse(SecureBaseModel):
    total: int
    items: List[PaymentTermRead]

    model_config = ConfigDict(from_attributes=True)


class PaymentTermImportResult(SecureBaseModel):
    total_imported: int
    total_errors: int
    imported: list
    errors: list

    model_config = ConfigDict(from_attributes=True)
