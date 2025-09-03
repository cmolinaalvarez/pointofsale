from pydantic import BaseModel
from typing import Optional
from uuid import UUID

class StockBase(BaseModel):
    product_id: UUID
    warehouse_id: UUID
    quantity: float 
    reserved: float    
    min_stock: float
    max_stock: float
    user_id: UUID

class StockCreate(StockBase):
    pass  # Todos los campos requeridos ya están en el base

# UPDATE (PUT)
class StockUpdate(StockBase):
    pass  # Igual, si son los mismos campos que BrandBase

class StockRead(StockBase):
    id: int

    class Config:
        from_attributes = True

class StockPatch(BaseModel):
    product_id: Optional[UUID] = None
    warehouse_id: Optional[UUID] = None
    quantity: Optional[float] = None
    reserver: Optional[float] = None    
    min_stock: Optional[float] = None
    max_stock: Optional[float] = None
    user_id: Optional[UUID] = None
