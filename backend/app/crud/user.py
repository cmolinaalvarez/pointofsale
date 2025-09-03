from __future__ import annotations

"""CRUD de Usuario con auditoría (actor vs. usuario objetivo).

Separa claramente:
- user_id : ID del usuario objetivo (registro modificado / consultado)
- actor_id: ID del usuario autenticado que realiza la acción (para auditoría)
"""

import logging
from datetime import datetime
from typing import Optional, Tuple
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate, UserPatch
from app.utils.audit import log_action

logger = logging.getLogger(__name__)


async def create_user(db: AsyncSession, user_in: UserCreate, actor_id: UUID) -> Tuple[User, object]:
    """Crea un usuario y registra auditoría (actor = creador)."""
    try:
        user = User(**user_in.model_dump(), user_id=actor_id)
        db.add(user)
        await db.flush()  # obtiene user.id
        log = await log_action(
            db,
            action="CREATE",
            entity="User",
            entity_id=user.id,
            description=f"Usuario creado: {user.full_name}",
            user_id=actor_id,
        )
        return user, log
    except Exception as e:
        await db.rollback()
        logger.exception("[create_user] Error creando usuario", exc_info=True)
        raise


async def get_users(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    active: Optional[bool] = None,
    actor_id: Optional[UUID] = None,
) -> dict:
    """Lista paginada con filtros y auditoría opcional."""
    try:
        query = select(User)
        if search:
            query = query.where(User.full_name.ilike(f"%{search}%"))
        if active is not None:
            query = query.where(User.active == active)

        total_result = await db.execute(select(func.count()).select_from(query.subquery()))
        total = total_result.scalar_one()

        result = await db.execute(query.order_by(User.email).offset(skip).limit(limit))
        items = result.scalars().all()

        if actor_id:
            await log_action(
                db,
                action="GETALL",
                entity="User",
                description=f"Listó usuarios search='{search}' active={active} skip={skip} limit={limit}",
                user_id=actor_id,
            )
        return {"total": total, "items": items}
    except SQLAlchemyError as e:
        await db.rollback()
        logger.error("[get_users] Error BD", exc_info=True)
        raise
    except Exception:
        await db.rollback()
        logger.exception("[get_users] Error inesperado", exc_info=True)
        raise


async def get_user_by_id(db: AsyncSession, user_id: UUID, actor_id: Optional[UUID] = None) -> User:
    """Obtiene un usuario y registra auditoría (actor)."""
    try:
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalars().first()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
        if actor_id:
            await log_action(
                db,
                action="GETID",
                entity="User",
                entity_id=user.id,
                description=f"Consultó usuario: {user.full_name}",
                user_id=actor_id,
            )
        return user
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        await db.rollback()
        logger.error("[get_user_by_id] Error BD", exc_info=True)
        raise HTTPException(status_code=500, detail="Error de base de datos")
    except Exception:
        await db.rollback()
        logger.exception("[get_user_by_id] Error inesperado", exc_info=True)
        raise HTTPException(status_code=500, detail="Error interno")


async def update_user(
    db: AsyncSession,
    user_in: UserUpdate,
    user_id: UUID,
    actor_id: UUID,
) -> Tuple[Optional[User], Optional[object]]:
    """Actualización completa (PUT). Retorna (usuario, log) o (None, None) si no existe."""
    try:
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalars().first()
        if not user:
            return None, None

        cambios = []
        if user.full_name != user_in.full_name:
            dup = await db.execute(
                select(User).where(User.full_name == user_in.full_name, User.id != user_id)
            )
            if dup.scalars().first():
                raise HTTPException(status_code=400, detail="Nombre ya usado por otro usuario")
            cambios.append(f"full_name: '{user.full_name}' -> '{user_in.full_name}'")
            user.full_name = user_in.full_name

        if user.active != user_in.active:
            cambios.append(f"active: {user.active} -> {user_in.active}")
            user.active = user_in.active
        if user.superuser != user_in.superuser:
            cambios.append(f"superuser: {user.superuser} -> {user_in.superuser}")
            user.superuser = user_in.superuser

        if not cambios:
            return user, None

        user.updated_at = datetime.utcnow()
        log = await log_action(
            db,
            action="UPDATE",
            entity="User",
            entity_id=user.id,
            description="; ".join(cambios),
            user_id=actor_id,
        )
        await db.flush()
        return user, log
    except HTTPException:
        raise
    except IntegrityError as e:
        await db.rollback()
        logger.error("[update_user] Integridad", exc_info=True)
        raise HTTPException(status_code=400, detail=str(e.orig))
    except SQLAlchemyError:
        await db.rollback()
        logger.error("[update_user] Error BD", exc_info=True)
        raise HTTPException(status_code=500, detail="Error de base de datos")
    except Exception:
        await db.rollback()
        logger.exception("[update_user] Error inesperado", exc_info=True)
        raise HTTPException(status_code=500, detail="Error interno")


async def patch_user(
    db: AsyncSession,
    user_in: UserPatch,
    user_id: UUID,
    actor_id: UUID,
) -> Tuple[Optional[User], Optional[object]]:
    """Actualización parcial (PATCH)."""
    try:
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalars().first()
        if not user:
            return None, None

        data = user_in.model_dump(exclude_unset=True)
        cambios = []
        for field, value in data.items():
            if hasattr(user, field):
                old = getattr(user, field)
                if old != value:
                    cambios.append(f"{field}: '{old}' -> '{value}'")
                    setattr(user, field, value)

        if not cambios:
            return user, None

        user.updated_at = datetime.utcnow()
        log = await log_action(
            db,
            action="PATCH",
            entity="User",
            entity_id=user.id,
            description="; ".join(cambios),
            user_id=actor_id,
        )
        await db.flush()
        return user, log
    except HTTPException:
        raise
    except IntegrityError as e:
        await db.rollback()
        logger.error("[patch_user] Integridad", exc_info=True)
        raise HTTPException(status_code=400, detail=str(e.orig))
    except SQLAlchemyError:
        await db.rollback()
        logger.error("[patch_user] Error BD", exc_info=True)
        raise HTTPException(status_code=500, detail="Error de base de datos")
    except Exception:
        await db.rollback()
        logger.exception("[patch_user] Error inesperado", exc_info=True)
    raise HTTPException(status_code=500, detail="Error interno")
