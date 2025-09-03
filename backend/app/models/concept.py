import uuid
import enum
from sqlalchemy import Enum as SAEnum
from typing import Optional
from sqlalchemy import String, Boolean, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

class ConceptTypeEnum(str, enum.Enum):
    E = "Entrada"
    S = "Salida"
    N = "Neutral"

class Concept(Base):
    __tablename__ = "concepts"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String, index=True, unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    concept_type: Mapped[ConceptTypeEnum] = mapped_column(
        SAEnum(ConceptTypeEnum, name="concept_type_enum", native_enum=True, validate_strings=True),
        nullable=False,
    )
    debit_account_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("accounts.id"), nullable=False)
    credit_account_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("accounts.id"), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=True)
    
    # ✅ Relaciones para obtener nombres de cuentas
    debit_account = relationship("Account", foreign_keys=[debit_account_id], lazy="joined")
    credit_account = relationship("Account", foreign_keys=[credit_account_id], lazy="joined")