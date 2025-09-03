# app/models/product.py
import uuid
import enum
from sqlalchemy import Enum as SAEnum
from datetime import datetime
from sqlalchemy import String, Float, Boolean, DateTime, UniqueConstraint, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, NUMERIC
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.db.base import Base

class ProductType(str, enum.Enum):
    UNI = "UNI" #Unico
    COM = "COM" #Compuesto

# =============== PRODUCTO ===============
class Product(Base):
    __tablename__ = "products"
    __table_args__ = (
        UniqueConstraint("code", name="uq_products_code"),
        UniqueConstraint("barcode", name="uq_products_barcode"),
    )

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    code: Mapped[str] = mapped_column(String(60), nullable=False, unique=True, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(String(255))
    
    product_type: Mapped[ProductType] = mapped_column(
        SAEnum(ProductType, name="product_type", native_enum=True, validate_strings=True),
        nullable=False,
        server_default=ProductType.UNI.value,  # <- default en DB
    )

    category_id: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("categories.id"), index=True)
    brand_id:    Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("brands.id"), index=True)
    unit_id:     Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("units.id"), index=True)
    user_id:     Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.id"), index=True)

    cost:        Mapped[float] = mapped_column(NUMERIC(14, 2), nullable=False)  # dinero => NUMERIC
    price:       Mapped[float] = mapped_column(NUMERIC(14, 2), nullable=False)
    percent_tax: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    barcode:   Mapped[str | None] = mapped_column(String(64), unique=True)
    image_url: Mapped[str | None] = mapped_column(String(255))

    negative_stock: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    active:         Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # relaciones de catálogo (opcional back_populates si lo configuras)
    # category = relationship("Category", lazy="selectin")
    # brand    = relationship("Brand", lazy="selectin")
    # unit     = relationship("Unit", lazy="selectin")
    # user     = relationship("User", lazy="selectin")
