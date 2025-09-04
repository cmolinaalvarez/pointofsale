import uuid
from datetime import datetime, timezone
from typing import List, Optional, TYPE_CHECKING
from enum import Enum

from sqlalchemy import String, Boolean, DateTime, Text, ForeignKey, JSON, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.user import User


class RoleTypeEnum(str, Enum):
    ADMIN = "admin"
    MANAGER = "manager"
    EMPLOYEE = "employee"
    CASHIER = "cashier"
    VIEWER = "viewer"
    API_USER = "api_user"
    SUPERVISOR = "supervisor"
    AUDITOR = "auditor"
    SYSTEM = "system"
    USER = "user"

class Role(Base):
    __tablename__ = "roles"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Cambiado: antes era String(20)
    role_type: Mapped[RoleTypeEnum] = mapped_column(
        SAEnum(
            RoleTypeEnum,
            name="role_type_enum",
            values_callable=lambda enum_cls: [m.value for m in enum_cls],  # asegura minúsculas
        ),
        nullable=False,
        index=True,
        default=RoleTypeEnum.VIEWER,          # default en ORM
        server_default="viewer"           # default en DB (asegura no nulo si se omite en INSERT)
    )
    
    # lista JSON de scopes, p.ej. ["read:products","write:sales"]
    scopes: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)

    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    active:   Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
   
    # ID del usuario que creó o modificó este parámetro (referencia externa a tabla users)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=True)

    # users: Mapped[List["User"]] = relationship("User", back_populates="role", foreign_keys="User.role_id", lazy="selectin")
    users: Mapped[List["User"]] = relationship(
        "User",
        foreign_keys="User.role_id",
        lazy="selectin"
    )
    creator: Mapped[Optional["User"]] = relationship("User", foreign_keys=[user_id], lazy="selectin")

    def __repr__(self) -> str:
        return f"<Role name={self.name!r} type={self.role_type!r}>"

    @property
    def scope_list(self) -> List[str]:
        return list(self.scopes or [])

    @scope_list.setter
    def scope_list(self, scopes: List[str]) -> None:
        self.scopes = list(scopes)

    @validates("role_type_enum")
    def _validate_role_type_enum(self, key, value):
        if value is None:
            return RoleTypeEnum.VIEWER
        if isinstance(value, RoleTypeEnum):
            return value
        try:
            return RoleTypeEnum(str(value).lower())
        except ValueError:
            raise ValueError(f"role_type_enum inválido: {value}")
  
