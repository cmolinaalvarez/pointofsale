# ========================================================
# MODELO: AuditLog
# Descripción: Registra eventos importantes en la base de datos.
# Ejemplos de eventos: LOGIN, CREATE, UPDATE, DELETE, LOGOUT, etc.
# ========================================================
from typing import Optional, TYPE_CHECKING
from datetime import datetime
import uuid

from sqlalchemy import String, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from app.db.base import Base  # Base declarativa asincrónica moderna

if TYPE_CHECKING:
    from app.models.user import User

class AuditLog(Base):
    __tablename__ = "audit_logs"  # Nombre real de la tabla en PostgreSQL

    # UUID autogenerado como clave primaria
    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # Acción ejecutada: LOGIN, CREATE, UPDATE, DELETE, LOGOUT, etc.
    action: Mapped[str] = mapped_column(String(50), nullable=False)

    # Nombre del modelo afectado (ej: 'Invoice', 'Product', 'User')
    entity: Mapped[str] = mapped_column(String(50), nullable=False)

    # ID del registro afectado (opcional)
    entity_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True), nullable=True
    )

    # Descripción detallada de lo que ocurrió
    description: Mapped[str] = mapped_column(Text, nullable=False)

    # Usuario responsable (UUID como clave foránea al modelo User)
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )

    # Fecha y hora de creación automática (UTC)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    # Relación hacia el modelo User (si se desea acceder al usuario desde el log)
    user: Mapped[Optional["User"]] = relationship(
        "User",
        lazy="selectin"
    )
