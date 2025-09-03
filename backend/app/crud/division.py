from sqlalchemy.future import select
from uuid import UUID
from app.models.division import Division
from app.schemas.division import DivisionCreate, DivisionUpdate, DivisionPatch
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
from app.models.country import Country

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/divisions", tags=["Divisions"])

async def create_division(db: AsyncSession, division_in: DivisionCreate, user_id: UUID):
    try:
        division = Division(**division_in.model_dump(), user_id=user_id)
        db.add(division)
        await db.flush()
    except Exception as e:
        logger.exception("Error al crear la división")  # Solo errores
        raise
    log = None
    try:
        description = (
            f"División creada: {division.name} "
            f"(id={division.id}, code={division.code}, country_id={division.country_id}, country_code={division.country_code}, \
              iso_3166_2={division.iso_3166_2}, active={division.active})"
        )
        audit_level = await get_audit_level(db)    # Decidir si registrar el log según el nivel
        if audit_level > 1:
            log = await log_action(
                db,
                action="CREATE",
                entity="Division",
                entity_id=division.id,
                description=description,
                user_id=division.user_id
            )
    except Exception as e:
        logger.exception("Error al crear el log de auditoría")  # Solo errores
        raise
    print(log)
    return division, log

# GET ALL
async def get_divisions(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    active: Optional[bool] = None,
    user_id: Optional[UUID] = None,  # Para auditoría
) -> dict:
    """
    Retorna una lista paginada de subdivisións, con soporte para búsqueda por nombre y filtro por estado activo.
    Incluye el nombre de la división asociada.
    """
    try:
        # Hacemos LEFT JOIN con Country para obtener el nombre (incluye divisiones sin país)
        query = (
            select(Division, Country.name)
            .outerjoin(Country, Division.country_id == Country.id)
        )

        if search:
            query = query.where(Division.name.ilike(f"%{search}%"))
        if active is not None:
            query = query.where(Division.active == active)

        # Calcular total de resultados
        total_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(total_query)
        total = total_result.scalar_one()

        # Obtener las subdivisións paginadas con nombre de división
        result = await db.execute(
            query.offset(skip).limit(limit).order_by(Division.name)
        )
        rows = result.all()
        # Construimos la lista con el nombre de la división
        divisions = [
            {
                "id": dv.id,
                "code": dv.code,
                "name": dv.name,
                "country_code": dv.country_code,
                "iso_3166_2": dv.iso_3166_2,
                "country_id": dv.country_id,   # <-- Este campo es obligatorio
                "country_name": country_name or "Sin país asignado",  # Manejo de None
                "active": dv.active,
                "created_at": dv.created_at,
                "updated_at": dv.updated_at,
                "user_id": dv.user_id,
            }
            for dv, country_name in rows
        ]
        
        audit_level = await get_audit_level(db)
        if audit_level > 2 and user_id:
            await log_action(
                db,
                action="GETALL",
                entity="Division",
                description=f"Consulta de divisiones - filtros: search='{search}', active={active}, skip={skip}, limit={limit}",
                user_id=user_id,
            )
        return {"total": total, "items": divisions}
    except SQLAlchemyError as e:
        await db.rollback()
        logging.exception("Error de base de datos en get_divisions", exc_info=True)
        raise
    except Exception as e:
        await db.rollback()
        logging.exception("Error inesperado en get_subdivisións", exc_info=True)
        raise  
  
async def get_division_by_id(
    db: AsyncSession,
    division_id: UUID,
    user_id: UUID = None  # Permite auditoría solo si hay user_id
) -> Division:
    """
    Recupera una división por su UUID y registra auditoría si se encuentra.

    Args:
        db (AsyncSession): Sesión de base de datos asincrónica.
        division_id (UUID): ID de la división a buscar.
        user_id (UUID, opcional): Usuario que realiza la consulta (para registrar auditoría).

    Returns:
        Division: Objeto encontrado.

    Raises:
        HTTPException:
            - 404 si no se encuentra la división.
            - 500 si ocurre un error de base de datos.
    """
    try:
        result = await db.execute(select(Division).where(Division.id == division_id))
        division = result.scalars().first()

        if not division:
            logger.warning(f"[GET_BRAND_BY_ID] División no encontrada: {division_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"División con ID {division_id} no encontrada"
            )
            
        audit_level = await get_audit_level(db)    # Decidir si registrar el log según el nivel
        if audit_level > 2 and user_id:
            # Registrar auditoría si hay user_id
            if user_id:
                await log_action(
                    db,
                    action="GETID",
                    entity="Division",
                    entity_id=division.id,
                    description=f"Consultó división: {division.name}",
                    user_id=user_id
                )
            # No commit aquí, solo flush si log_action lo requiere
            db.flush()
        return division

    except SQLAlchemyError as e:
        await db.rollback()
        logger.error(f"[GET_BRAND_BY_ID] Error al consultar división {division_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al consultar la división"
        )
    except Exception as e:
        await db.rollback()
        logger.exception(f"[GET_BRAND_BY_ID] Error inesperado al consultar división {division_id}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ocurrió un error inesperado al consultar la división"
        )       


# UPDATE (PUT = total)
async def update_division(
    db: AsyncSession,
    division_id: UUID,
    division_in: 'DivisionUpdate',
    user_id: UUID
):
    """
    Actualiza una división y construye el log de auditoría.
    - Retorna (division_actualizada, log_de_auditoria)
    - Si no hay cambios, retorna (division, None)
    - Si la división no existe, retorna (None, None)
    """
    try:
        # 1. Busca la división existente
        result = await db.execute(select(Division).where(Division.id == division_id))
        division = result.scalars().first()
        if not division:
            logger.info(f"[update_division] División {division_id} no encontrada.")
            return None, None

        cambios = []
        
        # 1. Detecta y aplica otros cambios
        if division.code != division_in.code:
            cambios.append(f"código: '{division.code}' → '{division_in.code}'")
            division.code = division_in.code
       
        # 2. Valida unicidad de nombre SOLO si cambia el nombre
        if division.name != division_in.name:
            existing = await db.execute(
                select(Division).where(Division.name == division_in.name, Division.id != division_id)
            )
            if existing.scalars().first():
                logger.warning(f"[update_division] Nombre duplicado: {division_in.name}")
                raise HTTPException(
                    status_code=400,
                    detail=f"Ya existe una división con el nombre '{division_in.name}'."
                )
            cambios.append(f"nombre: '{division.name}' → '{division_in.name}'")
            division.name = division_in.name
            
        # 3. Detecta y aplica otros cambios
        if division.country_id != division_in.country_id:
            cambios.append(f"country_id: '{division.country_id}' → '{division_in.country_id}'")
            division.country_id = division_in.country_id               

        if division.active != division_in.active:
            cambios.append(f"activo: {division.active} → {division_in.active}")
            division.active = division_in.active

        # 4. Si no hay cambios, retorna solo la división (sin log)
        if not cambios:
            logger.info(f"[update_division] No hubo cambios en la división {division_id}.")
            return division, None

        # 5. Actualiza el timestamp
        division.updated_at = datetime.utcnow()
        audit_level = await get_audit_level(db)    # Decidir si registrar el log según el nivel
        if audit_level >= 1 and user_id:
            # 6. Crea el log de auditoría con la descripción de cambios
            log = await log_action(
                db,
                action="UPDATE",
                entity="Division",
                entity_id=division.id,
                description=f"Cambios en la División: {', '.join(cambios)}",
                user_id=user_id,
            )

        await db.flush()  # Asegura que ambos cambios estén en la sesión

        logger.info(f"[update_division] División {division_id} actualizada por usuario {user_id}.")
        return division, log

    except IntegrityError as e:
        await db.rollback()
        logger.error("[update_division] Error de integridad: %s", e, exc_info=True)
        raise HTTPException(
            status_code=400,
            detail="Error de integridad de datos: " + str(e.orig)
        )
    except SQLAlchemyError as e:
        await db.rollback()
        logger.error("[update_division] Error SQLAlchemy: %s", e, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Error en la base de datos"
        )
    except Exception as e:
        await db.rollback()
        logger.exception("[update_division] Error inesperado", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error interno: {str(e)}"
        )
        
async def patch_division(
    db: AsyncSession,
    division_id: UUID,
    division_in: 'DivisionPatch',
    user_id: UUID  # ¡Para log de auditoría!
) -> tuple:
    """
    Actualiza parcialmente una división (PATCH) y registra log de auditoría.
    Retorna (division_actualizada, log_de_auditoria) o (None, None) si no existe.
    """
    try:
         # 1. Busca la división existente
        result = await db.execute(select(Division).where(Division.id == division_id))
        division = result.scalars().first()
        if not division:
            logger.warning(f"[patch_division] Marca {division_id} no encontrada.")
            return None, None

        data = division_in.dict(exclude_unset=True)
        cambios = []

        for field, value in data.items():
            if hasattr(division, field):
                old_value = getattr(division, field)
                if old_value != value:
                    cambios.append(f"{field}: '{old_value}' → '{value}'")
                    setattr(division, field, value)

        if not cambios:
            logger.info(f"[patch_division] No hubo cambios en la división {division_id}.")
            return division, None

        division.updated_at = datetime.utcnow()
        audit_level = await get_audit_level(db)    # Decidir si registrar el log según el nivel
        if audit_level >= 1 and user_id:
            log = await log_action(
                db,
                action="PATCH",
                entity="Division",
                entity_id=division.id,
                description=f"Actualización parcial: {', '.join(cambios)}",
                user_id=user_id,
            )

        await db.flush()  # Asegura que los cambios y log estén listos para commit

        logger.info(f"[patch_division] División {division_id} parcheada por usuario {user_id}. Cambios: {cambios}")
        return division, log

    except IntegrityError as e:
        await db.rollback()
        logger.error("[patch_division] Error de integridad: %s", e, exc_info=True)
        raise HTTPException(
            status_code=400,
            detail="Error de integridad de datos: " + str(e.orig)
        )
    except SQLAlchemyError as e:
        await db.rollback()
        logger.error("[patch_division] Error SQLAlchemy: %s", e, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Error en la base de datos"
        )
    except Exception as e:
        await db.rollback()
        logger.exception("[patch_division] Error inesperado", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error interno: {str(e)}"
        )
