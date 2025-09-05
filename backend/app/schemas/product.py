# app/schemas/product.py
from __future__ import annotations

from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime
from decimal import Decimal
from pydantic import Field, ConfigDict

from app.schemas.security_schemas import (
    EntityBase,      # code, name, description, active + validaciones comunes
    SecureBaseModel,
    CODE_RX,         # regex seguro para "code"/SKU
)

# ---------- Base ----------
class ProductBase(EntityBase):
    # Relaciones (opcionales)
    brand_id: Optional[UUID] = None
    category_id: Optional[UUID] = None
    subcategory_id: Optional[UUID] = None
    group_id: Optional[UUID] = None
    subgroup_id: Optional[UUID] = None
    unit_id: Optional[UUID] = None

    # Identificadores / textos
    sku: Optional[str] = Field(None, min_length=1, max_length=50, pattern=CODE_RX)
    barcode: Optional[str] = Field(None, min_length=1, max_length=64, pattern=r"^[0-9A-Za-z\-\._ ]+$")

    # Númericos
    price: Optional[Decimal] = Field(None, ge=0)
    cost: Optional[Decimal] = Field(None, ge=0)
    tax_rate: Optional[float] = Field(None, ge=0.0, le=1.0)  # 0..1 = 0%..100%
    stock_min: Optional[float] = Field(None, ge=0.0)
    stock_max: Optional[float] = Field(None, ge=0.0)

# ---------- Entrada ----------
class ProductCreate(ProductBase):
    pass

class ProductUpdate(ProductBase):
    pass

class ProductPatch(SecureBaseModel):
    # Campos parciales (todos opcionales)
    code: Optional[str] = Field(None, min_length=1, max_length=EntityBase.CODE_MAX, pattern=CODE_RX)
    name: Optional[str] = Field(None, min_length=1, max_length=EntityBase.NAME_MAX)
    description: Optional[str] = Field(None, max_length=EntityBase.DESC_MAX)
    active: Optional[bool] = None

    brand_id: Optional[UUID] = None
    category_id: Optional[UUID] = None
    subcategory_id: Optional[UUID] = None
    group_id: Optional[UUID] = None
    subgroup_id: Optional[UUID] = None
    unit_id: Optional[UUID] = None

    sku: Optional[str] = Field(None, min_length=1, max_length=50, pattern=CODE_RX)
    barcode: Optional[str] = Field(None, min_length=1, max_length=64, pattern=r"^[0-9A-Za-z\-\._ ]+$")

    price: Optional[Decimal] = Field(None, ge=0)
    cost: Optional[Decimal] = Field(None, ge=0)
    tax_rate: Optional[float] = Field(None, ge=0.0, le=1.0)
    stock_min: Optional[float] = Field(None, ge=0.0)
    stock_max: Optional[float] = Field(None, ge=0.0)

# ---------- Salida ----------
class ProductRead(SecureBaseModel):
    id: UUID
    code: str
    name: str
    description: Optional[str] = None
    active: bool

    brand_id: Optional[UUID] = None
    category_id: Optional[UUID] = None
    subcategory_id: Optional[UUID] = None
    group_id: Optional[UUID] = None
    subgroup_id: Optional[UUID] = None
    unit_id: Optional[UUID] = None

    sku: Optional[str] = None
    barcode: Optional[str] = None
    price: Optional[Decimal] = None
    cost: Optional[Decimal] = None
    tax_rate: Optional[float] = None
    stock_min: Optional[float] = None
    stock_max: Optional[float] = None

    created_at: datetime
    updated_at: Optional[datetime] = None
    user_id: Optional[UUID] = None

    # Ignora cualquier campo extra que venga del ORM
    model_config = ConfigDict(from_attributes=True, extra="ignore")

class ProductListResponse(SecureBaseModel):
    total: int
    items: List[ProductRead]

    model_config = ConfigDict(from_attributes=True)
  
# Al final de app/schemas/product.py
from app.schemas.security_schemas import ImportResult as _GenericImportResult

class ProductImportResult(_GenericImportResult): 
    pass

