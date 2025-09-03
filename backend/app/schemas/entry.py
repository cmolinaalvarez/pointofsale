from __future__ import annotations

from uuid import UUID
from datetime import datetime
from typing import List, Optional
from decimal import Decimal

from pydantic import BaseModel, Field, ConfigDict, field_validator


# ================================
# ÍTEMS DE ENTRADA
# ================================
class EntryItemBase(BaseModel):
    product_id: UUID
    quantity: Decimal = Field(..., description="Cantidad (permite decimales)")
    subtotal: Decimal = Field(..., ge=0)
    discount: Decimal = Field(..., ge=0)
    tax: Decimal = Field(..., ge=0)
    total: Decimal = Field(..., ge=0)

    # Normaliza a no-negativo y evita -0.00
    @field_validator("quantity", "subtotal", "discount", "tax", "total")
    @classmethod
    def _non_negative(cls, v: Decimal) -> Decimal:
        # Si quieres redondeo fijo, haz: v.quantize(Decimal("0.0000")) según tu escala
        if v < 0:
            raise ValueError("Debe ser no negativo")
        return v


class EntryItemCreate(EntryItemBase):
    pass


class EntryItemRead(EntryItemBase):
    id: UUID
    model_config = ConfigDict(from_attributes=True)  # Pydantic v2


# ================================
# ENTRADA (CABECERA)
# ================================
class EntryBase(BaseModel):
    document_id: UUID
    purchase_id: Optional[UUID] = None
    third_party_id: UUID
    concept_id: UUID
    user_id: UUID
    warehouse_id: UUID
    subtotal: Decimal = Field(..., ge=0)
    discount: Decimal = Field(..., ge=0)
    tax: Decimal = Field(..., ge=0)
    total: Decimal = Field(..., ge=0)

    @field_validator("subtotal", "discount", "tax", "total")
    @classmethod
    def _non_negative(cls, v: Decimal) -> Decimal:
        if v < 0:
            raise ValueError("Debe ser no negativo")
        return v


class EntryCreate(EntryBase):
    active: Optional[bool] = True
    items: List[EntryItemCreate]  # requerido al crear


class EntryRead(EntryBase):
    id: UUID
    created_at: datetime
    entry_number: str
    active: bool
    items: List[EntryItemRead] = Field(default_factory=list)
    model_config = ConfigDict(from_attributes=True)


