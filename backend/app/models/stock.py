# ============================================================
# IMPORTACIONES NECESARIAS
# ============================================================
# Tipos de columna: String, Boolean para texto y verdadero/falso
# DateTime para fechas y ForeignKey para claves foráneas
from sqlalchemy import String, Boolean, DateTime, ForeignKey, Numeric
from sqlalchemy.sql import func  # Para usar funciones como "func.now()"

# Tipado ORM moderno con Mapped y mapped_column
from sqlalchemy.orm import Mapped, mapped_column

# Modelo base común para heredar
from app.db.base import Base

# Importamos el tipo GUID_ID, que representa un identificador único (UUID)
# Esto se usa en lugar de un entero para el campo `id`
import uuid
from sqlalchemy.dialects.postgresql import UUID

# ============================================================
# MODELO DE LA TABLA 'stocks' (existencias)
# ============================================================
class Stock(Base):
    __tablename__ = "stocks"  # Nombre real de la tabla
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    warehouse_id:Mapped[UUID] = mapped_column(ForeignKey("warehouses.id"), nullable=False)
    product_id:Mapped[UUID] = mapped_column(ForeignKey("products.id"), nullable=False)
    quantity: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    min_stock: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    max_stock: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    reserved: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), onupdate=func.now(), nullable=True)