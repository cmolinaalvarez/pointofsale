# app/models/accounts.py
from sqlalchemy.orm import relationship
import uuid
import enum
from datetime import datetime

from sqlalchemy import String, Boolean, Enum, ForeignKey, DateTime
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


# ======================================================
# ENUM para tipo de cuenta
# ======================================================
class AccountTypeEnum(str, enum.Enum):
    ACT = "Activo"  # Activo
    PAS = "Pasivo"  # Pasivo
    PAT = "Patrimonio"  # Patrimonio
    ING = "Ingresos"  # Ingresos
    GAS = "Gastos"  # Gastos
    COS = "Costos"  # Costos
    ORD = "Orden"  # Ordén


class Account(Base):
    __tablename__ = "accounts"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # Ajusta el length si quieres (ej. 30). Index + unique está OK.
    code: Mapped[str] = mapped_column(String(30), unique=True, index=True, nullable=False)

    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)

    account_type: Mapped[AccountTypeEnum] = mapped_column(
        Enum(
            AccountTypeEnum,
            name="account_type",        # nombre del tipo ENUM en PostgreSQL
            native_enum=True,           # crea un tipo enum nativo en PG
            validate_strings=True,      # valida que el string pertenezca al Enum
        ),
        nullable=False,
    )
    
    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )

    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # onupdate aplica en UPDATE; server_default inicializa en INSERT
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=True
    )
    
    # Relaciones con Concept
    debit_concepts = relationship("Concept", foreign_keys="Concept.debit_account_id", back_populates="debit_account")
    credit_concepts = relationship("Concept", foreign_keys="Concept.credit_account_id", back_populates="credit_account")