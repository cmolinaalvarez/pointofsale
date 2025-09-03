import uuid
from datetime import datetime
from sqlalchemy import String, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base  # Tu base declarativa asincrónica

class Group(Base):
    __tablename__ = "groups"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        index=True,
        default=uuid.uuid4
    )

    code: Mapped[str] = mapped_column(
        String,
        index=True,
        unique=True,
        nullable=False
    )

    name: Mapped[str] = mapped_column(
        String,
        index=True,
        nullable=False
    )
    
    description: Mapped[str] = mapped_column(String, index=True, nullable=True)
    
    subcategory_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("subcategories.id"),
        nullable=False
    )

    active: Mapped[bool] = mapped_column(
        Boolean,
        default=True
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        onupdate=datetime.utcnow,
        nullable=True
    )

    # Relaciones ORM
    # Si necesitas relacionar Group con otra entidad, agrégalo aquí
    # Por ejemplo, para productos relacionados:
    # products: Mapped[list["Product"]] = relationship("Product", back_populates="group")

