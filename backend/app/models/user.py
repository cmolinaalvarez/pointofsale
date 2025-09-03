# app/models/user.py
import uuid
from datetime import datetime, timezone
from typing import List, Optional, TYPE_CHECKING

from sqlalchemy import String, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.role import Role


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    username: Mapped[str] = mapped_column(
        String(50), unique=True, index=True, nullable=False
    )
    email: Mapped[str] = mapped_column(
        String, unique=True, index=True, nullable=False
    )
    full_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    password: Mapped[str] = mapped_column(String, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # FK a roles (evita ciclo en migraciones con use_alter)
    role_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("roles.id", name="fk_users_role_id_roles", use_alter=True),
        nullable=True,
    )

    # Quién creó este usuario (self-FK, también con use_alter)
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", name="fk_users_user_id_users", use_alter=True),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=True,
    )

    # Relaciones
    # role: Mapped[Optional["Role"]] = relationship(
    #     "Role", back_populates="users", foreign_keys=[role_id], lazy="selectin"
    # )
    created_by: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[user_id],
        remote_side="User.id",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<User username={self.username!r} email={self.email!r}>"

    # @property
    # def scopes(self) -> List[str]:
    #     return self.role.scope_list if self.role else ["read"]

    # def has_scope(self, scope: str) -> bool:
    #     if self.superuser or (self.role and self.role.is_admin):
    #         return True
    #     return scope in self.scopes

    # def has_any_scope(self, scopes: List[str]) -> bool:
    #     return any(self.has_scope(s) for s in scopes)

    # def has_all_scopes(self, scopes: List[str]) -> bool:
    #     return all(self.has_scope(s) for s in scopes)
