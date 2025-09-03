# app/models/third_party.py
import uuid
import enum
from datetime import datetime

from sqlalchemy import String, Boolean, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.base import Base


# =========================
# Enums
# =========================
class ThirdPartyTypeEnum(str, enum.Enum):
    C = "C"  # Cliente
    P = "P"  # Proveedor
    A = "A"  # Ambos


class PersonTypeEnum(str, enum.Enum):
    N = "N"  # Natural
    J = "J"  # Jurídica
    A = "A"  # Ambos


# =========================
# Tercero
# =========================
class ThirdParty(Base):
    __tablename__ = "third_parties"
    __table_args__ = (
        UniqueConstraint("name", name="uq_third_parties_name"),
        UniqueConstraint("nit", name="uq_third_parties_nit"),
    )

    # PK UUID
    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )

    # Básicos
    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)

    third_party_type: Mapped[ThirdPartyTypeEnum] = mapped_column(
        SAEnum(ThirdPartyTypeEnum, name="third_party_type_enum", native_enum=True, validate_strings=True),
        nullable=False,
    )
    person_type: Mapped[PersonTypeEnum] = mapped_column(
        SAEnum(PersonTypeEnum, name="person_type_enum", native_enum=True, validate_strings=True),
        nullable=False,
    )

    contact_name: Mapped[str | None] = mapped_column(String(100))
    phone:        Mapped[str | None] = mapped_column(String(30))
    cell_phone:   Mapped[str | None] = mapped_column(String(30))
    email:        Mapped[str | None] = mapped_column(String(100), index=True)
    address:      Mapped[str | None] = mapped_column(String(200))

    # FKs (ajusta a UUID/Integer según tus tablas de catálogo)
    country_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("countries.id"), index=True
    )
    
    division_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("divisions.id"), index=True
    )
    
    municipality_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("municipalities.id"), index=True
    )

    nit: Mapped[str | None] = mapped_column(String(50))

    # Estado y auditoría mínima
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")

    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relaciones (opcional, habilítalas si tienes los modelos)
    # municipality = relationship("Municipality", lazy="selectin")
    # division     = relationship("Division", lazy="selectin")
    # country      = relationship("Country", lazy="selectin")
    # user         = relationship("User", lazy="selectin")

    def __repr__(self) -> str:
        return f"<ThirdParty(id={self.id}, name='{self.name}')>"
