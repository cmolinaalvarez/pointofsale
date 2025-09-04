from pydantic import Field
from uuid import UUID
from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from enum import Enum

from app.schemas.security_schemas import EntityBase, SecureBaseModel

class ProductType(str, Enum):
    UNI = "UNI"
    COM = "COM"

class ProductBase(EntityBase):
    # Campos extra de tu modelo (ajusta límites si quieres):
    product_type: ProductType
    sku: Optional[str] = Field(None, min_length=1, max_length=64)
    price: Decimal | float | int
    cost: Optional[Decimal | float | int] = None
    tax_percent: Optional[float] = Field(None, ge=0.0, le=100.0)
    barcode: Optional[str] = Field(None, max_length=64)
    image_url: Optional[str] = Field(None, max_length=255)
    negative_stock: bool = False

class ProductCreate(ProductBase):
    pass

class ProductUpdate(ProductBase):
    pass

class ProductPatch(SecureBaseModel):
    code: Optional[str] = Field(None, min_length=1, max_length=10)
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    active: Optional[bool] = None
    product_type: Optional[ProductType] = None
    sku: Optional[str] = Field(None, min_length=1, max_length=64)
    price: Optional[Decimal | float | int] = None
    cost: Optional[Decimal | float | int] = None
    tax_percent: Optional[float] = Field(None, ge=0.0, le=100.0)
    barcode: Optional[str] = Field(None, max_length=64)
    image_url: Optional[str] = Field(None, max_length=255)
    negative_stock: Optional[bool] = None

class ProductRead(SecureBaseModel):
    id: UUID
    code: str
    name: str
    description: Optional[str] = None
    active: bool
    product_type: ProductType
    sku: Optional[str] = None
    price: Decimal | float | int
    cost: Optional[Decimal | float | int] = None
    tax_percent: Optional[float] = None
    barcode: Optional[str] = None
    image_url: Optional[str] = None
    negative_stock: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    user_id: UUID
    category_id: Optional[UUID] = None
    brand_id: Optional[UUID] = None
    unit_id: Optional[UUID] = None

    class Config:
        from_attributes = True

class ProductListResponse(SecureBaseModel):
    total: int
    items: List[ProductRead]

    class Config:
        from_attributes = True

class ProductImportResult(SecureBaseModel):
    total_imported: int
    total_errors: int
    imported: list
    errors: list
