"""
CRUD operations for Role model

Este módulo contiene todas las operaciones CRUD para roles.
"""

import uuid
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from sqlalchemy import select, and_, or_, func, asc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from fastapi import HTTPException, status

from app.models.role import Role, RoleType
from app.models.user import User
from app.schemas.role import (
    RoleCreate, RoleUpdate, RolePatch
)
from app.utils.audit import log_action

logger = logging.getLogger(__name__)


class RoleCRUD:
    """CRUD operations for Role model"""

    async def get(self, db: AsyncSession, role_id: uuid.UUID, user_id: Optional[uuid.UUID] = None) -> Optional[Role]:
        """Obtener rol por ID"""
        try:
            result = await db.execute(
                select(Role)
                .options(selectinload(Role.users))
                .where(Role.id == role_id)
            )
            role = result.scalar_one_or_none()
            
            if role and user_id:
                await log_action(
                    db,
                    action="GETID",
                    entity="Role",
                    entity_id=role.id,
                    description=f"Consultó rol: {role.name}",
                    user_id=user_id
                )
                await db.flush()
                
            return role
            
        except SQLAlchemyError as e:
            logger.error(f"Error al obtener rol {role_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al consultar el rol"
            )

    async def get_by_name(self, db: AsyncSession, name: str) -> Optional[Role]:
        """Obtener rol por nombre"""
        try:
            result = await db.execute(
                select(Role)
                .where(Role.name == name)
            )
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            logger.error(f"Error al obtener rol por nombre {name}: {e}")
            raise

    async def get_multi(
        self,
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        role_type: Optional[RoleType] = None,
        active: Optional[bool] = None,
        search: Optional[str] = None,
        user_id: Optional[uuid.UUID] = None
    ) -> tuple[List[Role], int]:
        """Obtener múltiples roles con filtros"""
        try:
            query = select(Role).options(selectinload(Role.users))
            count_query = select(func.count(Role.id))

            # Aplicar filtros
            conditions = []
            
            if role_type:
                conditions.append(Role.role_type == role_type)
            
            if active is not None:
                conditions.append(Role.active == active)
                
            if search:
                search_condition = or_(
                    Role.name.ilike(f"%{search}%"),
                    Role.description.ilike(f"%{search}%")
                )
                conditions.append(search_condition)

            if conditions:
                query = query.where(and_(*conditions))
                count_query = count_query.where(and_(*conditions))

            # Ordenar por nombre
            query = query.order_by(asc(Role.name))

            # Paginación
            query = query.offset(skip).limit(limit)

            # Ejecutar consultas
            result = await db.execute(query)
            count_result = await db.execute(count_query)
            
            roles = result.scalars().all()
            total = count_result.scalar()

            # Registrar auditoría
            if user_id:
                await log_action(
                    db,
                    action="GETALL",
                    entity="Role",
                    description=f"Consulta de roles - filtros: search='{search}', active={active}, role_type={role_type}, skip={skip}, limit={limit}",
                    user_id=user_id
                )
                await db.flush()

            return list(roles), total
            
        except SQLAlchemyError as e:
            logger.error(f"Error al obtener roles: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error al consultar los roles"
            )

    async def create(self, db: AsyncSession, obj_in: RoleCreate, user_id: uuid.UUID) -> Role:
        """Crear nuevo rol"""
        try:
            # Verificar que el nombre no exista
            existing = await self.get_by_name(db, obj_in.name)
            if existing:
                raise ValueError(f"Ya existe un rol con el nombre '{obj_in.name}'")

            # Crear el rol con los campos del modelo actual
            db_obj = Role(
                name=obj_in.name,
                description=obj_in.description,
                role_type=(obj_in.role_type or RoleType.VIEWER),
                scopes=obj_in.scopes,
                is_admin=obj_in.is_admin,
                active=obj_in.active
            )
            db.add(db_obj)
            await db.commit()
            await db.refresh(db_obj)
            return db_obj
        except Exception as e:
            await db.rollback()
            raise

    async def update(
        self, 
        db: AsyncSession, 
        role_id: uuid.UUID, 
        obj_in: RoleUpdate,
        user_id: uuid.UUID
    ) -> tuple[Optional[Role], Optional[Any]]:
        """Actualizar rol existente"""
        try:
            # Buscar el rol existente
            db_obj = await self.get(db, role_id)
            if not db_obj:
                return None, None

            cambios = []

            # Verificar nombre único si se cambia
            if obj_in.name and obj_in.name != db_obj.name:
                existing = await self.get_by_name(db, obj_in.name)
                if existing:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Ya existe un rol con el nombre '{obj_in.name}'"
                    )
                cambios.append(f"nombre: '{db_obj.name}' → '{obj_in.name}'")

            # Detectar y aplicar cambios
            update_data = obj_in.dict(exclude_unset=True)
            
            for field, value in update_data.items():
                if field == "scopes" and isinstance(value, str):
                    # Permitir recibir coma-separado desde API
                    value = [v.strip() for v in value.split(",") if v.strip()]
                if hasattr(db_obj, field):
                    old_value = getattr(db_obj, field)
                    if old_value != value and value is not None:
                        cambios.append(f"{field}: '{old_value}' → '{value}'")
                        setattr(db_obj, field, value)

            # Si no hay cambios, retornar sin log
            if not cambios:
                logger.info(f"No hubo cambios en el rol {role_id}")
                return db_obj, None

            db_obj.updated_at = datetime.now(timezone.utc)

            # Crear log de auditoría
            log = await log_action(
                db,
                action="UPDATE",
                entity="Role",
                entity_id=db_obj.id,
                description=f"Cambios en el rol: {', '.join(cambios)}",
                user_id=user_id
            )

            await db.flush()
            await db.commit()
            await db.refresh(db_obj)
            return db_obj, log
            
        except HTTPException:
            raise
        except SQLAlchemyError as e:
            await db.rollback()
            logger.error(f"Error de base de datos al actualizar rol: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error en la base de datos"
            )

    async def patch(self, db: AsyncSession, role_id: uuid.UUID, obj_in: RolePatch, user_id: uuid.UUID) -> tuple[Optional[Role], Optional[Any]]:
        """Actualización parcial de rol"""
        try:
            db_obj = await self.get(db, role_id)
            if not db_obj:
                return None, None

            cambios = []
            update_data = obj_in.dict(exclude_unset=True)
            
            for field, value in update_data.items():
                if field == "scopes" and isinstance(value, str):
                    value = [v.strip() for v in value.split(",") if v.strip()]
                if hasattr(db_obj, field):
                    old_value = getattr(db_obj, field)
                    if old_value != value and value is not None:
                        cambios.append(f"{field}: '{old_value}' → '{value}'")
                        setattr(db_obj, field, value)

            if not cambios:
                logger.info(f"No hubo cambios en el rol {role_id}")
                return db_obj, None

            db_obj.updated_at = datetime.now(timezone.utc)

            log = await log_action(
                db,
                action="PATCH",
                entity="Role",
                entity_id=db_obj.id,
                description=f"Actualización parcial: {', '.join(cambios)}",
                user_id=user_id
            )

            await db.flush()
            await db.commit()
            await db.refresh(db_obj)
            return db_obj, log
            
        except SQLAlchemyError as e:
            await db.rollback()
            logger.error(f"Error al actualizar parcialmente rol: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error en la base de datos"
            )

    async def delete(self, db: AsyncSession, role_id: uuid.UUID, user_id: uuid.UUID) -> Dict[str, Any]:
        """Eliminar rol (solo si no tiene usuarios asignados)"""
        try:
            role = await self.get(db, role_id)
            if not role:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Rol no encontrado"
                )

            # Verificar que no tenga usuarios asignados
            user_count = await self.get_users_count(db, role_id)
            if user_count > 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"No se puede eliminar el rol. Tiene {user_count} usuarios asignados"
                )

            # Crear log antes de eliminar
            await log_action(
                db,
                action="DELETE",
                entity="Role",
                entity_id=role.id,
                description=f"Rol eliminado: {role.name}",
                user_id=user_id
            )

            await db.delete(role)
            await db.flush()
            
            logger.info(f"Rol {role_id} eliminado por usuario {user_id}")
            
            return {
                "success": True,
                "message": f"Rol '{role.name}' eliminado exitosamente",
                "affected_users": 0
            }
            
        except HTTPException:
            raise
        except SQLAlchemyError as e:
            await db.rollback()
            logger.error(f"Error al eliminar rol: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error en la base de datos"
            )

    async def get_users_count(self, db: AsyncSession, role_id: uuid.UUID) -> int:
        """Obtener cantidad de usuarios con este rol"""
        try:
            result = await db.execute(
                select(func.count(User.id))
                .where(User.role_id == role_id)
            )
            return result.scalar()
        except SQLAlchemyError as e:
            logger.error(f"Error al contar usuarios del rol {role_id}: {e}")
            return 0


# Instancia singleton
role_crud = RoleCRUD()