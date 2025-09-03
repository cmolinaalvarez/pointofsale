import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy import String, Boolean, DateTime, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.db.base import Base  # Tu base declarativa asíncrona

# =========================================================
# MODELO DE UNIDADES DE MEDIDA (UNITS) — ASÍNCRONO
# =========================================================
class Unit(Base):
    __tablename__ = "units"

    # ID primario autoincremental
    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        index=True,
        default=uuid.uuid4
    )

    # Nombre de la unidad (Ej: "Kilogramo", "Metro")
    name: Mapped[str] = mapped_column(String, index=True, nullable=False)

    # Descripción opcional (Ej: "Unidad de peso", "Unidad de longitud")
    description: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    # Símbolo de la unidad (Ej: "kg", "m", "lt") — debe ser único
    symbol: Mapped[str] = mapped_column(String(10), nullable=False, unique=True)

    # Estado activo/inactivo (soft delete)
    active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Usuario que creó o modificó la unidad (relación a users)
    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False
    )

    # Trazabilidad: fechas de creación y actualización
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(),
        onupdate=func.now(), nullable=False
    )