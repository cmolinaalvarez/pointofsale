from sqlalchemy.future import select
from uuid import UUID
from app.models.unit import Unit
from app.schemas.unit import UnitCreate, UnitUpdate, UnitPatch
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.audit_log import AuditLog
from datetime import datetime
from fastapi import HTTPException
from app.utils.audit import log_action
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from datetime import datetime
import logging
from sqlalchemy.future import select
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from fastapi import APIRouter,HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import logging
from sqlalchemy.exc import SQLAlchemyError
from app.utils.audit_level import get_audit_level

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/units", tags=["Units"])

async def create_unit(db: AsyncSession, unit_in: UnitCreate, user_id: UUID):
    try:
        unit = Unit(**unit_in.model_dump(), user_id=user_id)
        db.add(unit)
        await db.flush()
    except Exception as e:
        logger.exception("Error al crear la unidad")  # Solo errores
        raise
    log = None
    try:
        description = (
            f"Unidad creada: {unit.name} "
            f"(id={unit.id}, description={unit.description}, symbol={unit.symbol}, active={unit.active})"
        )
        audit_level = await get_audit_level(db)    # Decidir si registrar el log según el nivel
        if audit_level > 1:
            log = await log_action(
                db,
                action="CREATE",
                entity="Unit",
                entity_id=unit.id,
                description=description,
                user_id=unit.user_id
            )
    except Exception as e:
        logger.exception("Error al crear el log de auditoría")  # Solo errores
        raise
    print(log)
    return unit, log

# GET ALL
async def get_units(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    active: Optional[bool] = None,
    user_id: Optional[UUID] = None,  # Para auditoría
) -> dict:
    """
    Retorna una lista paginada de unidades, con soporte para búsqueda por nombre y filtro por estado activo.
    Registra la auditoría si es necesario.
    """
    try:
        query = select(Unit)

        if search:
            query = query.where(Unit.name.ilike(f"%{search}%"))
        if active is not None:
            query = query.where(Unit.active == active)

        # Calcular total de resultados
        total_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(total_query)
        total = total_result.scalar_one()

        # Obtener las unidades paginadas
        result = await db.execute(
            query.offset(skip).limit(limit).order_by(Unit.name)
        )
        units = result.scalars().all()
        audit_level = await get_audit_level(db)    # Decidir si registrar el log según el nivel
        if audit_level > 2 and user_id:
            await log_action(
                db,
                action="GETALL",
                entity="Unit",
                description=f"Consulta de unidades - filtros: search='{search}', active={active}, skip={skip}, limit={limit}",
                user_id=user_id,
            )
            # db.flush()
        return {"total": total, "items": units}
    except SQLAlchemyError as e:
        await db.rollback()
        logging.exception("Error de base de datos en get_units", exc_info=True)
        raise  # Puedes relanzar aquí y manejarlo en el endpoint
    except Exception as e:
        await db.rollback()
        logging.exception("Error inesperado en get_units", exc_info=True)
        raise
  
async def get_unit_by_id(
    db: AsyncSession,
    unit_id: UUID,
    user_id: UUID = None  # Permite auditoría solo si hay user_id
) -> Unit:
    """
    Recupera una unidad por su UUID y registra auditoría si se encuentra.

    Args:
        db (AsyncSession): Sesión de base de datos asincrónica.
        unit_id (UUID): ID de la unidad a buscar.
        user_id (UUID, opcional): Usuario que realiza la consulta (para registrar auditoría).

    Returns:
        Unit: Objeto encontrado.

    Raises:
        HTTPException:
            - 404 si no se encuentra la unidad.
            - 500 si ocurre un error de base de datos.
    """
    try:
        result = await db.execute(select(Unit).where(Unit.id == unit_id))
        unit = result.scalars().first()

        if not unit:
            logger.warning(f"[GET_BRAND_BY_ID] Unidad no encontrada: {unit_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Unidad con ID {unit_id} no encontrada"
            )
            
        audit_level = await get_audit_level(db)    # Decidir si registrar el log según el nivel
        if audit_level > 2 and user_id:
            # Registrar auditoría si hay user_id
            if user_id:
                await log_action(
                    db,
                    action="GETID",
                    entity="Unit",
                    entity_id=unit.id,
                    description=f"Consultó unidad: {unit.name}",
                    user_id=user_id
                )
            # No commit aquí, solo flush si log_action lo requiere
            db.flush()
        return unit

    except SQLAlchemyError as e:
        await db.rollback()
        logger.error(f"[GET_BRAND_BY_ID] Error al consultar unidad {unit_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al consultar la unidad"
        )
    except Exception as e:
        await db.rollback()
        logger.exception(f"[GET_BRAND_BY_ID] Error inesperado al consultar unidad {unit_id}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ocurrió un error inesperado al consultar la unidad"
        )       


# UPDATE (PUT = total)
async def update_unit(
    db: AsyncSession,
    unit_id: UUID,
    unit_in: 'UnitUpdate',
    user_id: UUID
):
    """
    Actualiza una unidad y construye el log de auditoría.
    - Retorna (unit_actualizada, log_de_auditoria)
    - Si no hay cambios, retorna (unit, None)
    - Si la unidad no existe, retorna (None, None)
    """
    try:
        # 1. Busca la unidad existente
        result = await db.execute(select(Unit).where(Unit.id == unit_id))
        unit = result.scalars().first()
        if not unit:
            logger.info(f"[update_unit] Unidad {unit_id} no encontrada.")
            return None, None

        cambios = []

        # 1. Valida unicidad de nombre SOLO si cambia el nombre
        if unit.name != unit_in.name:
            existing = await db.execute(
                select(Unit).where(Unit.name == unit_in.name, Unit.id != unit_id)
            )
            if existing.scalars().first():
                logger.warning(f"[update_unit] Nombre duplicado: {unit_in.name}")
                raise HTTPException(
                    status_code=400,
                    detail=f"Ya existe una unidad con el nombre '{unit_in.name}'."
                )
            cambios.append(f"nombre: '{unit.name}' → '{unit_in.name}'")
            unit.name = unit_in.name
        
        # 2. Detecta y aplica otros cambios
        if unit.description != unit_in.description:
            cambios.append(f"code: '{unit.description}' → '{unit_in.description}'")
            unit.description = unit_in.description        
                
        # 3. Detecta y aplica otros cambios
        if unit.symbol != unit_in.symbol:
            cambios.append(f"symbol: '{unit.symbol}' → '{unit_in.symbol}'")
            unit.symbol = unit_in.symbol
        
        if unit.active != unit_in.active:
            cambios.append(f"activo: {unit.active} → {unit_in.active}")
            unit.active = unit_in.active

        # 4. Si no hay cambios, retorna solo la unidad (sin log)
        if not cambios:
            logger.info(f"[update_unit] No hubo cambios en la unidad {unit_id}.")
            return unit, None

        # 5. Actualiza el timestamp
        unit.updated_at = datetime.utcnow()
        audit_level = await get_audit_level(db)    # Decidir si registrar el log según el nivel
        if audit_level >= 1 and user_id:
            # 6. Crea el log de auditoría con la descripción de cambios
            log = await log_action(
                db,
                action="UPDATE",
                entity="Unit",
                entity_id=unit.id,
                description=f"Cambios en la unidad: {', '.join(cambios)}",
                user_id=user_id,
            )

        await db.flush()  # Asegura que ambos cambios estén en la sesión

        logger.info(f"[update_unit] Unidad {unit_id} actualizada por usuario {user_id}.")
        return unit, log

    except IntegrityError as e:
        await db.rollback()
        logger.error("[update_unit] Error de integridad: %s", e, exc_info=True)
        raise HTTPException(
            status_code=400,
            detail="Error de integridad de datos: " + str(e.orig)
        )
    except SQLAlchemyError as e:
        await db.rollback()
        logger.error("[update_unit] Error SQLAlchemy: %s", e, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Error en la base de datos"
        )
    except Exception as e:
        await db.rollback()
        logger.exception("[update_unit] Error inesperado", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error interno: {str(e)}"
        )
        
async def patch_unit(
    db: AsyncSession,
    unit_id: UUID,
    unit_in: 'UnitPatch',
    user_id: UUID  # ¡Para log de auditoría!
) -> tuple:
    """
    Actualiza parcialmente una unidad (PATCH) y registra log de auditoría.
    Retorna (unit_actualizada, log_de_auditoria) o (None, None) si no existe.
    """
    try:
         # 1. Busca la unidad existente
        result = await db.execute(select(Unit).where(Unit.id == unit_id))
        unit = result.scalars().first()
        if not unit:
            logger.warning(f"[patch_unit] Unidad {unit_id} no encontrada.")
            return None, None

        data = unit_in.dict(exclude_unset=True)
        cambios = []

        for field, value in data.items():
            if hasattr(unit, field):
                old_value = getattr(unit, field)
                if old_value != value:
                    cambios.append(f"{field}: '{old_value}' → '{value}'")
                    setattr(unit, field, value)

        if not cambios:
            logger.info(f"[patch_unit] No hubo cambios en la unidad {unit_id}.")
            return unit, None

        unit.updated_at = datetime.utcnow()
        audit_level = await get_audit_level(db)    # Decidir si registrar el log según el nivel
        if audit_level >= 1 and user_id:
            log = await log_action(
                db,
                action="PATCH",
                entity="Unit",
                entity_id=unit.id,
                description=f"Actualización parcial: {', '.join(cambios)}",
                user_id=user_id,
            )

        await db.flush()  # Asegura que los cambios y log estén listos para commit

        logger.info(f"[patch_unit] Unidad {unit_id} parcheada por usuario {user_id}. Cambios: {cambios}")
        return unit, log

    except IntegrityError as e:
        await db.rollback()
        logger.error("[patch_unit] Error de integridad: %s", e, exc_info=True)
        raise HTTPException(
            status_code=400,
            detail="Error de integridad de datos: " + str(e.orig)
        )
    except SQLAlchemyError as e:
        await db.rollback()
        logger.error("[patch_unit] Error SQLAlchemy: %s", e, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Error en la base de datos"
        )
    except Exception as e:
        await db.rollback()
        logger.exception("[patch_unit] Error inesperado", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error interno: {str(e)}"
        )
