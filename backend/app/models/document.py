import uuid
import enum
from sqlalchemy import Enum as SAEnum
from datetime import datetime
from sqlalchemy import String, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base  # Asegúrate de que sea tu base asincrónica

# =========================
# Enums
# =========================
class DocumentTypeEnum(str, enum.Enum):
    E = "Entrada"
    S = "Salida"
    N = "Neutral"  

class Document(Base):
    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        index=True,
        default=uuid.uuid4
    )
    code: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String, index=True, nullable=False, unique=True)
    description: Mapped[str] = mapped_column(String, index=True, nullable=True)
    document_type: Mapped[DocumentTypeEnum] = mapped_column(
        SAEnum(DocumentTypeEnum, name="document_type_enum", native_enum=True, validate_strings=True),
        nullable=False,
    )
    prefix: Mapped[str] = mapped_column(String, unique=True, nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=True)

    # Relaciones
    # user: Mapped["User"] = relationship("User")
    # products: Mapped[list["Product"]] = relationship("Product", back_populates="category")
    # subcategories: Mapped[list["SubCategory"]] = relationship("SubCategory", back_populates="category")