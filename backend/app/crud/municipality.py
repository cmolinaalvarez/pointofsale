from sqlalchemy.future import select
from uuid import UUID
from app.models.municipality import Municipality
from app.schemas.municipality import MunicipalityCreate, MunicipalityUpdate, MunicipalityPatch
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
from app.models.division import Division
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import logging
from sqlalchemy.exc import SQLAlchemyError
from app.utils.audit_level import get_audit_level
from app.models.division import Division

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/municipalities", tags=["Municipalities"])

async def create_municipality(db: AsyncSession, municipality_in: MunicipalityCreate, user_id: UUID):
    try:
        municipality = Municipality(**municipality_in.model_dump(), user_id=user_id)
        db.add(municipality)
        await db.flush()
    except Exception as e:
        logger.exception("Error al crear el municipio")  # Solo errores
        raise
    log = None
    try:
        description = (
            f"Municipios creada: {municipality.name} "
            f"(id={municipality.id}, code={municipality.code}, division_id={municipality.division_id}, division_code={municipality.division_code}, active={municipality.active})"
        )
        audit_level = await get_audit_level(db)    # Decidir si registrar el log según el nivel
        if audit_level > 1:
            log = await log_action(
                db,
                action="CREATE",
                entity="Municipality",
                entity_id=municipality.id,
                description=description,
                user_id=municipality.user_id
            )
    except Exception as e:
        logger.exception("Error al crear el log de auditoría")  # Solo errores
        raise
    print(log)
    return municipality, log

# GET ALL
async def get_municipalities(
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
            select(Municipality, Division.name)
            .outerjoin(Division, Municipality.division_id == Division.id)
        )

        if search:
            query = query.where(Municipality.name.ilike(f"%{search}%"))
        if active is not None:
            query = query.where(Municipality.active == active)

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
        municipalities = [
            {
                "id": dv.id,
                "code": dv.code,
                "name": dv.name,
                "division_code": dv.division_code,
                "division_id": dv.division_id,   # <-- Este campo es obligatorio
                "division_name": division_name or "Sin división asignada",  # Manejo de None
                "active": dv.active,
                "created_at": dv.created_at,
                "updated_at": dv.updated_at,
                "user_id": dv.user_id,
            }
            for dv, division_name in rows
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
        return {"total": total, "items": municipalities}
    except SQLAlchemyError as e:
        await db.rollback()
        logging.exception("Error de base de datos en get_divisions", exc_info=True)
        raise
    except Exception as e:
        await db.rollback()
        logging.exception("Error inesperado en get_subdivisións", exc_info=True)
        raise  
  
async def get_municipality_by_id(
    db: AsyncSession,
    municipality_id: UUID,
    user_id: UUID = None  # Permite auditoría solo si hay user_id
) -> Municipality:
    """
    Recupera una municipio por su UUID y registra auditoría si se encuentra.

    Args:
        db (AsyncSession): Sesión de base de datos asincrónica.
        municipality_id (UUID): ID de el municipio a buscar.
        user_id (UUID, opcional): Usuario que realiza la consulta (para registrar auditoría).

    Returns:
        Municipality: Objeto encontrado.

    Raises:
        HTTPException:
            - 404 si no se encuentra el municipio.
            - 500 si ocurre un error de base de datos.
    """
    try:
        result = await db.execute(select(Municipality).where(Municipality.id == municipality_id))
        municipality = result.scalars().first()

        if not municipality:
            logger.warning(f"[GET_BRAND_BY_ID] Municipios no encontrada: {municipality_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Municipios con ID {municipality_id} no encontrada"
            )
            
        audit_level = await get_audit_level(db)    # Decidir si registrar el log según el nivel
        if audit_level > 2 and user_id:
            # Registrar auditoría si hay user_id
            if user_id:
                await log_action(
                    db,
                    action="GETID",
                    entity="Municipality",
                    entity_id=municipality.id,
                    description=f"Consultó municipio: {municipality.name}",
                    user_id=user_id
                )
            # No commit aquí, solo flush si log_action lo requiere
            db.flush()
        return municipality

    except SQLAlchemyError as e:
        await db.rollback()
        logger.error(f"[GET_BRAND_BY_ID] Error al consultar municipio {municipality_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al consultar el municipio"
        )
    except Exception as e:
        await db.rollback()
        logger.exception(f"[GET_BRAND_BY_ID] Error inesperado al consultar municipio {municipality_id}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ocurrió un error inesperado al consultar el municipio"
        )       


# UPDATE (PUT = total)
async def update_municipality(
    db: AsyncSession,
    municipality_id: UUID,
    municipality_in: 'MunicipalityUpdate',
    user_id: UUID
):
    """
    Actualiza una municipio y construye el log de auditoría.
    - Retorna (municipality_actualizada, log_de_auditoria)
    - Si no hay cambios, retorna (municipality, None)
    - Si el municipio no existe, retorna (None, None)
    """
    try:
        # 1. Busca el municipio existente
        result = await db.execute(select(Municipality).where(Municipality.id == municipality_id))
        municipality = result.scalars().first()
        if not municipality:
            logger.info(f"[update_municipality] Municipios {municipality_id} no encontrada.")
            return None, None

        cambios = []
        
        # 1. Detecta y aplica otros cambios
        if municipality.code != municipality_in.code:
            cambios.append(f"código: '{municipality.code}' → '{municipality_in.code}'")
            municipality.code = municipality_in.code
       
        # 2. Valida unicidad de nombre SOLO si cambia el nombre
        if municipality.name != municipality_in.name:
            existing = await db.execute(
                select(Municipality).where(Municipality.name == municipality_in.name, Municipality.id != municipality_id)
            )
            if existing.scalars().first():
                logger.warning(f"[update_municipality] Nombre duplicado: {municipality_in.name}")
                raise HTTPException(
                    status_code=400,
                    detail=f"Ya existe una municipio con el nombre '{municipality_in.name}'."
                )
            cambios.append(f"nombre: '{municipality.name}' → '{municipality_in.name}'")
            municipality.name = municipality_in.name
            
        # 3. Detecta y aplica otros cambios
        if municipality.division_id != municipality_in.division_id:
            cambios.append(f"division_id: '{municipality.division_id}' → '{municipality_in.division_id}'")
            municipality.division_id = municipality_in.division_id               

        if municipality.active != municipality_in.active:
            cambios.append(f"activo: {municipality.active} → {municipality_in.active}")
            municipality.active = municipality_in.active

        # 4. Si no hay cambios, retorna solo el municipio (sin log)
        if not cambios:
            # Obtener el division_name para la respuesta
            division_query = await db.execute(
                select(Division.name).where(Division.id == municipality.division_id)
            )
            division_name = division_query.scalar_one_or_none()

            # Construir la respuesta con division_name incluido
            municipality_dict = {
                "id": municipality.id,
                "code": municipality.code,
                "name": municipality.name,
                "division_id": municipality.division_id,
                "division_code": municipality.division_code,
                "division_name": division_name or "Sin división asignada",
                "active": municipality.active,
                "user_id": municipality.user_id,
                "created_at": municipality.created_at,
                "updated_at": municipality.updated_at,
            }
            
            logger.info(f"[update_municipality] No hubo cambios en el municipio {municipality_id}.")
            return municipality_dict, None

        # 5. Actualiza el timestamp
        municipality.updated_at = datetime.utcnow()
        audit_level = await get_audit_level(db)    # Decidir si registrar el log según el nivel
        if audit_level >= 1 and user_id:
            # 6. Crea el log de auditoría con la descripción de cambios
            log = await log_action(
                db,
                action="UPDATE",
                entity="Municipality",
                entity_id=municipality.id,
                description=f"Cambios en el municipio: {', '.join(cambios)}",
                user_id=user_id,
            )

        await db.flush()  # Asegura que ambos cambios estén en la sesión

        # Obtener el division_name para la respuesta
        division_query = await db.execute(
            select(Division.name).where(Division.id == municipality.division_id)
        )
        division_name = division_query.scalar_one_or_none()

        # Construir la respuesta con division_name incluido
        municipality_dict = {
            "id": municipality.id,
            "code": municipality.code,
            "name": municipality.name,
            "division_id": municipality.division_id,
            "division_code": municipality.division_code,
            "division_name": division_name or "Sin división asignada",
            "active": municipality.active,
            "user_id": municipality.user_id,
            "created_at": municipality.created_at,
            "updated_at": municipality.updated_at,
        }

        logger.info(f"[update_municipality] Municipio {municipality_id} actualizado por usuario {user_id}.")
        return municipality_dict, log

    except IntegrityError as e:
        await db.rollback()
        logger.error("[update_municipality] Error de integridad: %s", e, exc_info=True)
        raise HTTPException(
            status_code=400,
            detail="Error de integridad de datos: " + str(e.orig)
        )
    except SQLAlchemyError as e:
        await db.rollback()
        logger.error("[update_municipality] Error SQLAlchemy: %s", e, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Error en la base de datos"
        )
    except Exception as e:
        await db.rollback()
        logger.exception("[update_municipality] Error inesperado", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error interno: {str(e)}"
        )
        
async def patch_municipality(
    db: AsyncSession,
    municipality_id: UUID,
    municipality_in: 'MunicipalityPatch',
    user_id: UUID  # ¡Para log de auditoría!
) -> tuple:
    """
    Actualiza parcialmente un municipio (PATCH) y registra log de auditoría.
    Retorna (municipality_actualizada, log_de_auditoria) o (None, None) si no existe.
    """
    try:
         # 1. Busca el municipio existente
        result = await db.execute(select(Municipality).where(Municipality.id == municipality_id))
        municipality = result.scalars().first()
        if not municipality:
            logger.warning(f"[patch_municipality] Marca {municipality_id} no encontrada.")
            return None, None

        data = municipality_in.dict(exclude_unset=True)
        cambios = []

        for field, value in data.items():
            if hasattr(municipality, field):
                old_value = getattr(municipality, field)
                if old_value != value:
                    cambios.append(f"{field}: '{old_value}' → '{value}'")
                    setattr(municipality, field, value)

        if not cambios:
            logger.info(f"[patch_municipality] No hubo cambios en el municipio {municipality_id}.")
            return municipality, None

        municipality.updated_at = datetime.utcnow()
        audit_level = await get_audit_level(db)    # Decidir si registrar el log según el nivel
        if audit_level >= 1 and user_id:
            log = await log_action(
                db,
                action="PATCH",
                entity="Municipality",
                entity_id=municipality.id,
                description=f"Actualización parcial: {', '.join(cambios)}",
                user_id=user_id,
            )

        await db.flush()  # Asegura que los cambios y log estén listos para commit

        logger.info(f"[patch_municipality] Municipio {municipality_id} parcheado por el usuario {user_id}. Cambios: {cambios}")
        return municipality, log

    except IntegrityError as e:
        await db.rollback()
        logger.error("[patch_municipality] Error de integridad: %s", e, exc_info=True)
        raise HTTPException(
            status_code=400,
            detail="Error de integridad de datos: " + str(e.orig)
        )
    except SQLAlchemyError as e:
        await db.rollback()
        logger.error("[patch_municipality] Error SQLAlchemy: %s", e, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Error en la base de datos"
        )
    except Exception as e:
        await db.rollback()
        logger.exception("[patch_municipality] Error inesperado", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error interno: {str(e)}"
        )
