# ============================================================
# IMPORTACIONES NECESARIAS
# ============================================================
from sqlalchemy import String, Boolean, DateTime, ForeignKey, Integer, Float
from sqlalchemy.sql import func
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base
import uuid
from sqlalchemy.dialects.postgresql import UUID

# ============================================================
# MODELO DE LA TABLA 'payment_terms' (términos de pago)
# ============================================================
class PaymentTerm(Base):
    __tablename__ = "payment_terms"

    # ID del término de pago (clave primaria)
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Código único del término de pago
    code: Mapped[str] = mapped_column(String(10), unique=True, index=True, nullable=False)
    
    # Nombre del término de pago
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    
    # Descripción del término de pago (opcional)
    description: Mapped[str] = mapped_column(String(500), nullable=True, default="")
    
    # Días netos para pago
    net_days: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    
    # Porcentaje de descuento por pago anticipado
    discount_percent: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    
    # Días para aplicar descuento
    discount_days: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    
    # Base de cálculo (Factura, Recepción, etc.)
    basis: Mapped[str] = mapped_column(String(20), nullable=False, default="Factura")
    
    # Estado del término de pago (activo o no)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # ID del usuario que creó el término de pago
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    
    # Fecha y hora de creación
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Fecha y hora de última actualización
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=True
    )