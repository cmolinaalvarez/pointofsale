import uuid
from datetime import datetime
from sqlalchemy import Boolean, Numeric, DateTime, String, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base  # Base declarativa asincrónica

# =============================
# Modelo principal de entrada de inventario
# =============================
class Entry(Base):
    __tablename__ = "entries"

    # ID principal tipo UUID
    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), 
        primary_key=True, 
        default=uuid.uuid4, 
        index=True
    )

    # Relaciones externas (UUID en vez de Integer)
    document_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), 
        ForeignKey("documents.id"), 
        nullable=False
    )
    
    purchase_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), 
        ForeignKey("purchases.id"), 
        nullable=True
    )
    third_party_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), 
        ForeignKey("third_parties.id"), 
        nullable=False
    )
    concept_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), 
        ForeignKey("concepts.id"), 
        nullable=False
    )
    warehouse_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), 
        ForeignKey("warehouses.id"), 
        nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), 
        ForeignKey("users.id"), 
        nullable=False
    )

    # Numeración
    sequence_number: Mapped[int] = mapped_column(nullable=False)  # Número secuencial interno
    entry_number: Mapped[str] = mapped_column(String(20), index=True, nullable=False)  # Ej: ENT-2025-00001

    # Totales financieros
    subtotal: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    discount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    tax: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    total: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)

    # Estado y trazabilidad
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, onupdate=datetime.utcnow, nullable=True)

    # Relación con los ítems de entrada
    items = relationship("EntryItem", back_populates="entry")


# =============================
# Modelo detalle de productos en la entrada
# =============================
class EntryItem(Base):
    __tablename__ = "entry_items"

    __table_args__ = (
        UniqueConstraint("entry_id", "product_id", name="uix_entry_product"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), 
        primary_key=True, 
        default=uuid.uuid4, 
        index=True
    )

    # Relaciones
    entry_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), 
        ForeignKey("entries.id"), 
        nullable=False
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), 
        ForeignKey("products.id"), 
        nullable=False
    )

    # Información financiera por ítem
    quantity: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    subtotal: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    discount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    tax: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    total: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)

    # Relaciones con modelos padres
    entry = relationship("Entry", back_populates="items")
    product = relationship("Product")
