import uuid
from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import String, Boolean, DateTime, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base  # Tu base declarativa asincrónica

if TYPE_CHECKING:
    from app.models.category import Category

class SubCategory(Base):
    __tablename__ = "subcategories"

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
        unique=True,
        nullable=False
    )
    description: Mapped[str] = mapped_column(String, index=True, nullable=True)
    category_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("categories.id"),
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
    # category: Mapped["Category"] = relationship(
    #     "Category",
    #     back_populates="subcategories"
    # )
    # Si quieres relación inversa, agrega en Category:
    # subcategories: Mapped[list["SubCategory"]] = relationship("SubCategory", back_populates="category")
