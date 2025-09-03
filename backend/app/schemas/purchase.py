from datetime import datetime, date
from typing import List, Optional
from decimal import Decimal
from uuid import UUID
from pydantic import BaseModel, ConfigDict

# Esquema base para los ítems de entrada
class PurchaseItemBase(BaseModel):
    product_id: UUID
    quantity: int
    price: Decimal
    expiration:str
    subtotal: Decimal
    discount: Decimal
    tax: Decimal
    expiration: date  # <-- tipo correcto
    total: Decimal

# Esquema para crear un ítem de entrada
class PurchaseItemCreate(PurchaseItemBase):
    pass

# Esquema para leer/devolver un ítem de entrada
class PurchaseItemRead(PurchaseItemBase):
    id: UUID
    class Config:
        from_attributes = True  # Pydantic v2

# Esquema base para entradas (purchase_invoice)
class PurchaseBase(BaseModel):
    document_id: UUID
    third_party_id: UUID
    concept_id: UUID
    payment_term_id: Optional[UUID] = None
    user_id: UUID
    subtotal: Decimal
    discount: Decimal
    tax: Decimal
    total: Decimal

# Esquema para crear una entrada (PurchaseCreate)
class PurchaseCreate(PurchaseBase):
    active: Optional[bool] = True
    items: List[PurchaseItemCreate]

# Esquema para leer/devolver una entrada desde la base de datos (PurchaseRead)
class PurchaseItemCreate(BaseModel):
    product_id: UUID
    quantity: int
    price: Decimal
    subtotal: Decimal
    discount: Decimal
    tax: Decimal
    total: Decimal
    expiration: Optional[date] = None       # <— opcional

class PurchaseItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    product_id: UUID
    quantity: int
    price: Decimal
    subtotal: Decimal
    discount: Decimal
    tax: Decimal
    total: Decimal
    expiration: Optional[date] = None       # <— opcional

class PurchaseRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    document_id: UUID
    third_party_id: UUID
    concept_id: UUID
    payment_term_id: UUID
    user_id: UUID
    subtotal: Decimal
    discount: Decimal
    tax: Decimal
    total: Decimal
    created_at: datetime
    purchase_number: str
    active: bool
    items: List[PurchaseItemRead] = []
      





