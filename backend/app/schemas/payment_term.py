from app.schemas.security_schemas import SecureBaseModel
from pydantic import Field, field_validator
from uuid import UUID
from typing import Optional, List
from datetime import datetime
import re

# BASE - Ahora hereda de SecureBaseModel
class PaymentTermBase(SecureBaseModel):    
    code: str = Field(..., min_length=1, max_length=10, description="Código único del término de pago")
    name: str = Field(..., min_length=1, max_length=100, description="Nombre del término de pago")
    description: Optional[str] = Field(None, max_length=500, description="Descripción del término de pago")
    net_days: int = Field(..., ge=0, description="Días netos para pago")
    discount_percent: float = Field(..., ge=0.0, le=100.0, description="Porcentaje de descuento por pago anticipado")
    discount_days: int = Field(..., ge=0, description="Días para aplicar descuento")
    basis: str = Field(..., min_length=1, max_length=20, description="Base de cálculo (Factura, Recepción, etc.)")
    active: bool = Field(True, description="Estado del término de pago")

    @field_validator('code')
    def validate_code(cls, v: str) -> str:
        # Expresión regular corregida
        if not re.match(r'^[A-Z0-9_-]+$', v):
            raise ValueError('El código solo puede contener letras mayúsculas, números, guiones y guiones bajos')
        return v.upper()

    @field_validator('basis')
    def validate_basis(cls, v: str) -> str:
        valid_bases = ["Factura", "Recepción", "Entrega", "Fin de mes"]
        if v not in valid_bases:
            raise ValueError(f'La base debe ser uno de: {", ".join(valid_bases)}')
        return v

# CREATE (POST) - Hereda de PaymentTermBase que ahora es seguro
class PaymentTermCreate(PaymentTermBase):
    pass

# UPDATE (PUT) - Hereda de PaymentTermBase que ahora es seguro
class PaymentTermUpdate(PaymentTermBase):
    pass

# PATCH (parcial) - Ahora hereda de SecureBaseModel también
class PaymentTermPatch(SecureBaseModel):
    code: Optional[str] = Field(None, min_length=1, max_length=10, description="Código único del término de pago")
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="Nombre del término de pago")
    description: Optional[str] = Field(None, max_length=500, description="Descripción del término de pago")
    net_days: Optional[int] = Field(None, ge=0, description="Días netos para pago")
    discount_percent: Optional[float] = Field(None, ge=0.0, le=100.0, description="Porcentaje de descuento por pago anticipado")
    discount_days: Optional[int] = Field(None, ge=0, description="Días para aplicar descuento")
    basis: Optional[str] = Field(None, min_length=1, max_length=20, description="Base de cálculo (Factura, Recepción, etc.)")
    active: Optional[bool] = Field(None, description="Estado del término de pago")

    @field_validator('code')
    def validate_code(cls, v: str) -> str:
        # Expresión regular corregida
        if not re.match(r'^[A-Z0-9_-]+$', v):
            raise ValueError('El código solo puede contener letras mayúsculas, números, guiones y guiones bajos')
        return v.upper()

    @field_validator('basis')
    def validate_basis(cls, v: str) -> str:
        valid_bases = ["Factura", "Fin de mes"]
        if v not in valid_bases:
            raise ValueError(f'La base debe ser uno de: {", ".join(valid_bases)}')
        return v

# LECTURA (GET) - Hereda de PaymentTermBase que ahora es seguro
class PaymentTermRead(PaymentTermBase):
    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# Respuesta para listado - Mantiene BaseModel ya que es solo para respuesta
class PaymentTermListResponse(SecureBaseModel):
    total: int
    items: List[PaymentTermRead]

    class Config:
        from_attributes = True

# Resultado de importación - Mantiene BaseModel ya que es solo para respuesta
class PaymentTermImportResult(SecureBaseModel):
    total_imported: int
    total_errors: int
    imported: list
    errors: list

    class Config:
        from_attributes = True