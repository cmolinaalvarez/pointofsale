# ============================================================
# IMPORTACIONES NECESARIAS
# ============================================================

from datetime import datetime
from uuid import UUID
from typing import TYPE_CHECKING  # 👈 Para evitar importaciones circulares al anotar tipos

from sqlalchemy import String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.base import Base  # Nuestra base declarativa moderna con SQLAlchemy 2.0
# Importamos el tipo GUID_ID, que representa un identificador único (UUID)
# Esto se usa en lugar de un entero para el campo `id`
import uuid
from sqlalchemy.dialects.postgresql import UUID
# ------------------------------------------------------------
# 👇 Importación condicional para anotaciones de tipo
# ------------------------------------------------------------
# TYPE_CHECKING es True solo durante el análisis de tipos estático (ej. mypy, editores).
# Esto permite evitar errores de importación circular en tiempo de ejecución,
# especialmente cuando `user.py` y `setting.py` se importan mutuamente.
# ------------------------------------------------------------
if TYPE_CHECKING:
    from app.models.user import User


# ============================================================
# MODELO DE CONFIGURACIÓN GENERAL DEL SISTEMA
# ============================================================
class Setting(Base):
    __tablename__ = "settings"  # Nombre de la tabla en la base de datos

    # ID autoincremental único del parámetro
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Clave del parámetro (por ejemplo: 'empresa_nombre', 'consecutive_by_year')
    # Debe ser única ya que representa la "llave lógica" del parámetro
    key: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)

    # Valor del parámetro: puede ser un string, un número serializado, JSON como texto, etc.
    value: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Tipo del parámetro: usado para saber cómo interpretar `value`
    # Ej: "string", "int", "bool", "json"
    type: Mapped[str] = mapped_column(String(20), default="string")

    # Descripción opcional para administración o referencia
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Estado de la marca (activa o no)
    active: Mapped[bool] = mapped_column(Boolean, default=True)

    # ID del usuario que creó o modificó este parámetro (referencia externa a tabla users)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), nullable=False)

    # Fecha de creación automática al insertar el registro
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),  # Valor generado por el servidor (PostgreSQL)
        nullable=False
    )

    # Fecha de actualización automática cuando se modifica el registro
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        onupdate=func.now(),  # Se actualiza automáticamente en UPDATE
        nullable=True
    )

    # --------------------------------------------------------
    # RELACIÓN CON EL MODELO User (opcional)
    # --------------------------------------------------------
    # Establece una relación con la tabla "users" para poder acceder al usuario
    # que creó/modificó este parámetro usando `setting.user`
    # --------------------------------------------------------
    #user: Mapped["User"] = relationship("User", back_populates="settings")
