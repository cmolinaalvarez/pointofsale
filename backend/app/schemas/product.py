from pydantic import BaseModel
from uuid import UUID
from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from enum import Enum

# ==============================
# ENUM
# ==============================
class ProductType(str, Enum):
    UNI = "UNI"  # Único
    COM = "COM"  # Compuesto

# ==============================
# BASE
# ==============================
class ProductBase(BaseModel):
    code: str
    name: str
    description: Optional[str] = None

    # En tu BD 'type' es NOT NULL (server_default='UNI')
    # Lo exponemos con default para que el POST pueda omitirlo si quiere.
    product_type: ProductType = ProductType.UNI

    category_id: Optional[UUID] = None
    brand_id: Optional[UUID] = None
    unit_id: Optional[UUID] = None

    cost: Decimal
    price: Decimal
    percent_tax: float = 0.0

    barcode: Optional[str] = None
    image_url: Optional[str] = None

    negative_stock: bool = False
    active: bool = True


# ==============================
# CREATE (POST)
# ==============================
class ProductCreate(ProductBase):
    pass


# ==============================
# UPDATE (PUT)
# ==============================
class ProductUpdate(ProductBase):
    active: bool  # explícito como en tu ConceptUpdate


# ==============================
# PATCH (parcial)
# ==============================
class ProductPatch(BaseModel):
    code: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None

    product_type: Optional[ProductType] = None

    category_id: Optional[UUID] = None
    brand_id: Optional[UUID] = None
    unit_id: Optional[UUID] = None

    cost: Optional[Decimal] = None
    price: Optional[Decimal] = None
    percent_tax: Optional[float] = None

    barcode: Optional[str] = None
    image_url: Optional[str] = None

    negative_stock: Optional[bool] = None
    active: Optional[bool] = None


# ==============================
# LECTURA (GET)
# ==============================
class ProductRead(ProductBase):
    id: UUID
    user_id: UUID
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ==============================
# LISTADO PAGINADO
# ==============================
class ProductListResponse(BaseModel):
    total: int
    items: List[ProductRead]

    class Config:
        from_attributes = True


# ==============================
# RESULTADO DE IMPORTACIÓN MASIVA
# ==============================
class ProductImportResult(BaseModel):
    total_imported: int
    total_errors: int
    imported: list
    errors: list
