# ============================================================
# IMPORTACIONES NECESARIAS
# ============================================================
# Tipos de columna: String, Boolean para texto y verdadero/falso
# DateTime para fechas y ForeignKey para claves foráneas
from sqlalchemy import String, Boolean, DateTime, ForeignKey
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
# MODELO DE LA TABLA 'brands' (marcas)
# ============================================================
class Brand(Base):
    __tablename__ = "brands"  # Nombre real de la tabla

    # ID de la marca (clave primaria)
    # - GUID_ID es un UUID (identificador único universal)
    # - mapped_column() define que esta columna es clave primaria
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    # Nombre de la marca (único, obligatorio, máximo 255 caracteres)
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)

    # Descripción de la marca (opcional, hasta 500 caracteres)
    # Este campo permite agregar detalles adicionales sobre la marca
    description: Mapped[str] = mapped_column(String(500), nullable=True)

    # Estado de la marca (activa o no)
    active: Mapped[bool] = mapped_column(Boolean, default=True)

    # ID del usuario que creó la marca
    # - Clave foránea que apunta a la tabla "users"
    # - UUID porque asumimos que `users.id` es UUID
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), nullable=False)

    # Fecha y hora de creación (se asigna automáticamente con func.now())
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


    # Definimos el campo `updated_at` usando `Mapped[DateTime]`, lo que indica que este atributo
    # es parte del modelo ORM y será mapeado a una columna en la base de datos con tipo `DateTime`.
    updated_at: Mapped[DateTime] = mapped_column(

    # Especificamos que la columna será de tipo `DateTime` y que manejará información de zona horaria (timezone=True),
    # lo cual es útil cuando trabajamos en aplicaciones distribuidas o con múltiples zonas horarias.
    DateTime(timezone=True),

    # `default=func.now()` indica que, cuando se cree un nuevo registro, el valor de esta columna se establecerá
    # automáticamente con la fecha y hora actual del servidor (func.now() es una función de SQL que equivale a "CURRENT_TIMESTAMP").
    server_default=func.now(),

    # `onupdate=func.now()` asegura que cada vez que el registro sea actualizado mediante un `UPDATE`,
    # esta columna se actualice automáticamente con la nueva fecha y hora del momento del cambio.
    # Es ideal para registrar la "última modificación".
    onupdate=func.now(),

    # Permitimos que el campo pueda quedar vacío si por alguna razón no se asigna (aunque generalmente no debería pasar).
    # Esto se hace por compatibilidad en algunas operaciones que no requieren actualización automática.
    nullable=True
    )
