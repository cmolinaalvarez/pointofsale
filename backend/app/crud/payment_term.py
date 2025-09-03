from sqlalchemy.future import select
from uuid import UUID
from app.models.payment_term import PaymentTerm
from app.schemas.payment_term import PaymentTermCreate, PaymentTermUpdate, PaymentTermPatch
from sqlalchemy.ext.asyncio import AsyncSession
from app.utils.audit import log_action
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from datetime import datetime
import logging
from sqlalchemy import func
from typing import Optional
from fastapi import HTTPException, status
from app.utils.audit_level import get_audit_level
from app.crud.base_security import CRUDSecurityBase
from app.utils.security_utils import SecurityUtils

logger = logging.getLogger(__name__)

class CRUDPaymentTerm(CRUDSecurityBase[PaymentTerm]):
    def __init__(self):
        super().__init__(PaymentTerm)
    
    async def create_payment_term(self, db: AsyncSession, payment_term_data: dict, user_id: UUID):
        """
        Crear término de pago con validaciones de seguridad
        """
        try:
            # Sanitizar datos de entrada
            sanitized_data = SecurityUtils.sanitize_data(payment_term_data)
            
            # Verificar si el código ya existe
            existing = await db.execute(
                select(PaymentTerm).where(PaymentTerm.code == sanitized_data['code'])
            )
            if existing.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Término de pago con código '{sanitized_data['code']}' ya existe"
                )
            
            # Agregar user_id a los datos
            sanitized_data['user_id'] = user_id
        
            # Crear el objeto usando el método base seguro
            payment_term = await self.create_with_security(db, sanitized_data, user_id)
            
            # Registrar auditoría si es necesario
            audit_level = await get_audit_level(db)
            if audit_level and audit_level >= 2:
                log = await log_action(
                    db=db,
                    action="CREATE",
                    table_name="payment_terms",
                    record_id=payment_term.id,
                    user_id=user_id,
                    old_values={},
                    new_values=SecurityUtils.obfuscate_sensitive_data(sanitized_data)
                )
                return payment_term, log
            
            return payment_term, None
            
        except HTTPException:
            await db.rollback()
            raise
        except Exception as e:
            await db.rollback()
            logger.error(f"Error al crear término de pago: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error interno al crear término de pago"
            )

    async def update_payment_term(
        self,
        db: AsyncSession,
        payment_term_id: UUID,
        payment_term_data: dict,
        user_id: UUID
    ):
        """
        Actualizar término de pago con validaciones de seguridad
        """
        try:
            # Sanitizar datos de entrada
            sanitized_data = SecurityUtils.sanitize_data(payment_term_data)
            
            # Buscar término de pago existente
            result = await db.execute(
                select(PaymentTerm).where(PaymentTerm.id == payment_term_id)
            )
            payment_term = result.scalars().first()
            
            if not payment_term:
                return None, None

            cambios = []
            old_values = {}
            
            # Verificar y aplicar cambios
            for field, value in sanitized_data.items():
                if hasattr(payment_term, field) and getattr(payment_term, field) != value:
                    old_values[field] = getattr(payment_term, field)
                    cambios.append(f"{field}: '{getattr(payment_term, field)}' → '{value}'")
                    setattr(payment_term, field, value)

            # Si no hay cambios, retornar sin hacer nada
            if not cambios:
                return payment_term, None

            # Actualizar timestamp
            payment_term.updated_at = datetime.utcnow()
            
            # Registrar auditoría
            audit_level = await get_audit_level(db)
            if audit_level >= 1:
                log = await log_action(
                    db,
                    action="UPDATE",
                    table_name="payment_terms",
                    record_id=payment_term.id,
                    user_id=user_id,
                    old_values=SecurityUtils.obfuscate_sensitive_data(old_values),
                    new_values=SecurityUtils.obfuscate_sensitive_data(sanitized_data),
                    description=f"Cambios en término de pago: {', '.join(cambios)}"
                )
            
            await db.flush()
            return payment_term, log
            
        except IntegrityError as e:
            await db.rollback()
            if "duplicate key" in str(e).lower() or "ix_payment_terms_code" in str(e):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Ya existe un término de pago con este código"
                )
            logger.error("Error de integridad al actualizar término de pago: %s", e, exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Error de integridad de datos"
            )
        except Exception as e:
            await db.rollback()
            logger.exception("Error inesperado al actualizar término de pago", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error inesperado al actualizar término de pago"
            )

# Instancia global del CRUD seguro
crud_payment_term = CRUDPaymentTerm()

# ========================================================================
# Funciones públicas (mantienen la interfaz original para los routers)
# ========================================================================

async def create_payment_term(db: AsyncSession, payment_term_data: dict, user_id: UUID):
    """
    Crear un nuevo término de pago (función pública)
    """
    return await crud_payment_term.create_payment_term(db, payment_term_data, user_id)

async def get_payment_terms(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    active: Optional[bool] = None,
    user_id: Optional[UUID] = None,
) -> dict:
    """
    Obtener lista de términos de pago con paginación y filtros
    """
    try:
        query = select(PaymentTerm)

        # Sanitizar búsqueda si existe
        if search:
            sanitized_search = SecurityUtils.sanitize_input(search)
            query = query.where(
                (PaymentTerm.name.ilike(f"%{sanitized_search}%")) | 
                (PaymentTerm.code.ilike(f"%{sanitized_search}%")) |
                (PaymentTerm.description.ilike(f"%{sanitized_search}%"))
            )
        
        if active is not None:
            query = query.where(PaymentTerm.active == active)

        # Calcular total
        total_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(total_query)
        total = total_result.scalar_one()

        # Obtener resultados paginados
        result = await db.execute(
            query.offset(skip).limit(limit).order_by(PaymentTerm.name)
        )
        payment_terms = result.scalars().all()
        
        # Registrar auditoría si es necesario
        audit_level = await get_audit_level(db)
        if audit_level > 2 and user_id:
            await log_action(
                db,
                action="GETALL",
                table_name="payment_terms",
                description=f"Consulta de términos de pago - filtros: search='{search}', active={active}, skip={skip}, limit={limit}",
                user_id=user_id,
            )
        
        return {"total": total, "items": payment_terms}
        
    except SQLAlchemyError as e:
        logger.error("Error de base de datos en get_payment_terms: %s", e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al obtener términos de pago"
        )
    except Exception as e:
        logger.exception("Error inesperado en get_payment_terms", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error inesperado al obtener términos de pago"
        )

async def get_payment_term_by_id(
    db: AsyncSession,
    payment_term_id: UUID,
    user_id: Optional[UUID] = None
) -> PaymentTerm:
    """
    Obtener un término de pago por ID
    """
    try:
        result = await db.execute(
            select(PaymentTerm).where(PaymentTerm.id == payment_term_id)
        )
        payment_term = result.scalars().first()

        if not payment_term:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Término de pago no encontrado"
            )
        
        # Registrar auditoría si es necesario
        audit_level = await get_audit_level(db)
        if audit_level > 2 and user_id:
            await log_action(
                db,
                action="GETID",
                table_name="payment_terms",
                record_id=payment_term.id,
                description=f"Consultó término de pago: {payment_term.name}",
                user_id=user_id
            )
        
        return payment_term
        
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error("Error de base de datos en get_payment_term_by_id: %s", e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al obtener término de pago"
        )
    except Exception as e:
        logger.exception("Error inesperado en get_payment_term_by_id", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error inesperado al obtener término de pago"
        )

async def update_payment_term(
    db: AsyncSession,
    payment_term_id: UUID,
    payment_term_data: dict,
    user_id: UUID
):
    """
    Actualizar un término de pago (función pública)
    """
    return await crud_payment_term.update_payment_term(db, payment_term_id, payment_term_data, user_id)

async def patch_payment_term(
    db: AsyncSession,
    payment_term_id: UUID,
    payment_term_data: dict,
    user_id: UUID
):
    """
    Actualizar parcialmente un término de pago (PATCH)
    """
    try:
        # Sanitizar datos de entrada
        sanitized_data = SecurityUtils.sanitize_data(payment_term_data)
        
        # Buscar término de pago existente
        result = await db.execute(
            select(PaymentTerm).where(PaymentTerm.id == payment_term_id)
        )
        payment_term = result.scalars().first()
        
        if not payment_term:
            return None, None

        cambios = []
        old_values = {}
        
        # Aplicar solo los campos proporcionados
        for field, value in sanitized_data.items():
            if hasattr(payment_term, field) and getattr(payment_term, field) != value:
                old_values[field] = getattr(payment_term, field)
                cambios.append(f"{field}: '{getattr(payment_term, field)}' → '{value}'")
                setattr(payment_term, field, value)

        # Si no hay cambios, retornar sin hacer nada
        if not cambios:
            return payment_term, None

        # Actualizar timestamp
        payment_term.updated_at = datetime.utcnow()
        
        # Registrar auditoría
        audit_level = await get_audit_level(db)
        if audit_level >= 1:
            log = await log_action(
                db,
                action="PATCH",
                table_name="payment_terms",
                record_id=payment_term.id,
                user_id=user_id,
                old_values=SecurityUtils.obfuscate_sensitive_data(old_values),
                new_values=SecurityUtils.obfuscate_sensitive_data(sanitized_data),
                description=f"Actualización parcial: {', '.join(cambios)}"
            )
        
        await db.flush()
        return payment_term, log
        
    except IntegrityError as e:
        await db.rollback()
        if "duplicate key" in str(e).lower() or "ix_payment_terms_code" in str(e):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ya existe un término de pago con este código"
            )
        logger.error("Error de integridad al actualizar término de pago: %s", e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error de integridad de datos"
        )
    except SQLAlchemyError as e:
        await db.rollback()
        logger.error("Error SQLAlchemy al actualizar término de pago: %s", e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error en la base de datos"
        )
    except Exception as e:
        await db.rollback()
        logger.exception("Error inesperado al actualizar término de pago", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error inesperado al actualizar término de pago"
        )

async def delete_payment_term(
    db: AsyncSession,
    payment_term_id: UUID,
    user_id: UUID
) -> bool:
    """
    Eliminar un término de pago
    """
    try:
        # Buscar término de pago existente
        result = await db.execute(
            select(PaymentTerm).where(PaymentTerm.id == payment_term_id)
        )
        payment_term = result.scalars().first()
        
        if not payment_term:
            return False

        # Registrar datos antes de eliminar para auditoría
        payment_term_data = {
            'code': payment_term.code,
            'name': payment_term.name,
            'description': payment_term.description
        }

        # Eliminar término de pago
        await db.delete(payment_term)
        
        # Registrar auditoría
        audit_level = await get_audit_level(db)
        if audit_level >= 1:
            await log_action(
                db,
                action="DELETE",
                table_name="payment_terms",
                record_id=payment_term_id,
                user_id=user_id,
                old_values=SecurityUtils.obfuscate_sensitive_data(payment_term_data),
                new_values={},
                description=f"Término de pago eliminado: {payment_term.name}"
            )
        
        await db.flush()
        return True
        
    except SQLAlchemyError as e:
        await db.rollback()
        logger.error("Error SQLAlchemy al eliminar término de pago: %s", e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error en la base de datos al eliminar término de pago"
        )
    except Exception as e:
        await db.rollback()
        logger.exception("Error inesperado al eliminar término de pago", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error inesperado al eliminar término de pago"
        )