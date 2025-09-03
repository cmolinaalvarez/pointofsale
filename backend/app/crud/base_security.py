from typing import Type, TypeVar, Generic, Optional, Dict, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from fastapi import HTTPException, status
import logging
from app.utils.security_utils import SecurityUtils

T = TypeVar('T')
logger = logging.getLogger(__name__)

class CRUDSecurityBase(Generic[T]):
    def __init__(self, model: Type[T]):
        self.model = model

    async def create_with_security(
        self, 
        db: AsyncSession, 
        obj_in: Dict[str, Any], 
        user_id: UUID,
        additional_checks: Optional[callable] = None
    ) -> T:
        """
        Crear objeto con validaciones de seguridad
        """
        try:
            # 1. Sanitizar datos de entrada
            sanitized_data = SecurityUtils.sanitize_data(obj_in)
            
            # 2. Validaciones adicionales personalizadas
            if additional_checks:
                await additional_checks(db, sanitized_data)
            
            # 3. Verificar unicidad si el modelo tiene campo 'code'
            if hasattr(self.model, 'code') and 'code' in sanitized_data:
                existing = await db.execute(
                    select(self.model).where(
                        getattr(self.model, 'code') == sanitized_data['code']
                    )
                )
                if existing.scalar_one_or_none():
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"{self.model.__name__} con este código ya existe"
                    )
            
            # 4. Crear objeto
            db_obj = self.model(**sanitized_data)
            if hasattr(db_obj, 'user_id'):
                db_obj.user_id = user_id
            
            db.add(db_obj)
            await db.flush()
            
            return db_obj
            
        except IntegrityError as e:
            await db.rollback()
            logger.error(f"Error de integridad al crear {self.model.__name__}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Error de integridad de datos"
            )
        except HTTPException:
            await db.rollback()
            raise
        except Exception as e:
            await db.rollback()
            logger.error(f"Error inesperado al crear {self.model.__name__}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error interno del servidor"
            )

    async def update_with_security(
        self,
        db: AsyncSession,
        obj_id: UUID,
        obj_in: Dict[str, Any],
        user_id: UUID
    ) -> Optional[T]:
        """
        Actualizar objeto con validaciones de seguridad
        """
        try:
            # 1. Sanitizar datos de entrada
            sanitized_data = SecurityUtils.sanitize_data(obj_in)
            
            # 2. Obtener objeto existente
            result = await db.execute(
                select(self.model).where(getattr(self.model, 'id') == obj_id)
            )
            db_obj = result.scalar_one_or_none()
            
            if not db_obj:
                return None
            
            # 3. Aplicar cambios
            for field, value in sanitized_data.items():
                if hasattr(db_obj, field):
                    setattr(db_obj, field, value)
            
            # 4. Actualizar timestamp si existe
            if hasattr(db_obj, 'updated_at'):
                from datetime import datetime
                db_obj.updated_at = datetime.utcnow()
            
            await db.flush()
            return db_obj
            
        except SQLAlchemyError as e:
            await db.rollback()
            logger.error(f"Error de base de datos al actualizar {self.model.__name__}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error en la base de datos"
            )