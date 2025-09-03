from sqlalchemy.future import select
from uuid import UUID
from app.models.country import Country
from app.schemas.country import CountryCreate, CountryUpdate, CountryPatch
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

router = APIRouter(prefix="/countries", tags=["Countries"])

async def create_country(db: AsyncSession, country_in: CountryCreate, user_id: UUID):
    try:
        country = Country(**country_in.model_dump(), user_id=user_id)
        db.add(country)
        await db.flush()
    except Exception as e:
        logger.exception("Error al crear el país")  # Solo errores
        raise
    log = None
    try:
        audit_level = await get_audit_level(db)    # Decidir si registrar el log según el nivel
        if audit_level > 1:
            description = (
                f"País creado: {country.name} "
                f"(id={country.id}, code={country.code}, active={country.active})"
            )
            log = await log_action(
                db,
                action="CREATE",
                entity="Country",
                entity_id=country.id,
                description=description,
                user_id=country.user_id
            )
    except Exception as e:
        logger.exception("Error al crear el log de auditoría")  # Solo errores
        raise
    print(log)
    return country, log

# GET ALL

async def get_countrys(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    active: Optional[bool] = None,
    user_id: Optional[UUID] = None,  # Para auditoría
) -> dict:
    """
    Retorna una lista paginada de paises, con soporte para búsqueda por nombre y filtro por estado activo.
    Registra la auditoría si es necesario.
    """
    try:
        query = select(Country)

        if search:
            query = query.where(Country.name.ilike(f"%{search}%"))
        if active is not None:
            query = query.where(Country.active == active)

        # Calcular total de resultados
        total_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(total_query)
        total = total_result.scalar_one()

        # Obtener las paíss paginadas
        result = await db.execute(
            query.offset(skip).limit(limit).order_by(Country.name)
        )
        countrys = result.scalars().all()
        audit_level = await get_audit_level(db)    # Decidir si registrar el log según el nivel
        if audit_level > 2 and user_id:
            await log_action(
                db,
                action="GETALL",
                entity="Country",
                description=f"Consulta de países - filtros: search='{search}', active={active}, skip={skip}, limit={limit}",
                user_id=user_id,
            )
            # db.flush()
        return {"total": total, "items": countrys}
    except SQLAlchemyError as e:
        await db.rollback()
        logging.exception("Error de base de datos en get_countries", exc_info=True)
        raise  # Puedes relanzar aquí y manejarlo en el endpoint
    except Exception as e:
        await db.rollback()
        logging.exception("Error inesperado en get_countries", exc_info=True)
        raise
  
async def get_country_by_id(
    db: AsyncSession,
    country_id: UUID,
    user_id: UUID = None  # Permite auditoría solo si hay user_id
) -> Country:
    """
    Recupera un país por su UUID y registra auditoría si se encuentra.

    Args:
        db (AsyncSession): Sesión de base de datos asincrónica.
        country_id (UUID): ID de la país a buscar.
        user_id (UUID, opcional): Usuario que realiza la consulta (para registrar auditoría).

    Returns:
        Country: Objeto encontrado.

    Raises:
        HTTPException:
            - 404 si no se encuentra la país.
            - 500 si ocurre un error de base de datos.
    """
    try:
        result = await db.execute(select(Country).where(Country.id == country_id))
        country = result.scalars().first()

        if not country:
            logger.warning(f"[GET_BRAND_BY_ID] país no encontrada: {country_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"País con ID {country_id} no encontrada"
            )
            
        audit_level = await get_audit_level(db)    # Decidir si registrar el log según el nivel
        if audit_level > 2 and user_id:
            # Registrar auditoría si hay user_id
            if user_id:
                await log_action(
                    db,
                    action="GETID",
                    entity="Country",
                    entity_id=country.id,
                    description=f"Consultó país: {country.name}",
                    user_id=user_id
                )
            # No commit aquí, solo flush si log_action lo requiere
            db.flush()
        return country

    except SQLAlchemyError as e:
        await db.rollback()
        logger.error(f"[GET_BRAND_BY_ID] Error al consultar país {country_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al consultar la país"
        )
    except Exception as e:
        await db.rollback()
        logger.exception(f"[GET_BRAND_BY_ID] Error inesperado al consultar país {country_id}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ocurrió un error inesperado al consultar la país"
        )       


# UPDATE (PUT = total)
async def update_country(
    db: AsyncSession,
    country_id: UUID,
    country_in: 'CountryUpdate',
    user_id: UUID
):
    """
    Actualiza una país y construye el log de auditoría.
    - Retorna (country_actualizada, log_de_auditoria)
    - Si no hay cambios, retorna (country, None)
    - Si la país no existe, retorna (None, None)
    """
    try:
        # 1. Busca la país existente
        result = await db.execute(select(Country).where(Country.id == country_id))
        country = result.scalars().first()
        if not country:
            logger.info(f"[update_country] País {country_id} no encontrado.")
            return None, None

        cambios = []
        
        # 1. Detecta y aplica otros cambios
        if country.code != country_in.code:
            cambios.append(f"código: '{country.code}' → '{country_in.code}'")
            country.code = country_in.code

        # 2. Valida unicidad de nombre SOLO si cambia el nombre
        if country.name != country_in.name:
            existing = await db.execute(
                select(Country).where(Country.name == country_in.name, Country.id != country_id)
            )
            if existing.scalars().first():
                logger.warning(f"[update_country] Nombre duplicado: {country_in.name}")
                raise HTTPException(
                    status_code=400,
                    detail=f"Ya existe una país con el nombre '{country_in.name}'."
                )
            cambios.append(f"nombre: '{country.name}' → '{country_in.name}'")
            country.name = country_in.name

        # 3. Detecta y aplica otros cambios
        if country.active != country_in.active:
            cambios.append(f"activo: {country.active} → {country_in.active}")
            country.active = country_in.active

        # 4. Si no hay cambios, retorna solo la país (sin log)
        if not cambios:
            logger.info(f"[update_country] No hubo cambios en el país {country_id}.")
            return country, None

        # 5. Actualiza el timestamp
        country.updated_at = datetime.utcnow()
        audit_level = await get_audit_level(db)    # Decidir si registrar el log según el nivel
        if audit_level >= 1 and user_id:
            # 6. Crea el log de auditoría con la descripción de cambios
            log = await log_action(
                db,
                action="UPDATE",
                entity="Country",
                entity_id=country.id,
                description=f"Cambios en la País: {', '.join(cambios)}",
                user_id=user_id,
            )

        await db.flush()  # Asegura que ambos cambios estén en la sesión

        logger.info(f"[update_country] País {country_id} actualizada por usuario {user_id}.")
        return country, log

    except IntegrityError as e:
        await db.rollback()
        logger.error("[update_country] Error de integridad: %s", e, exc_info=True)
        raise HTTPException(
            status_code=400,
            detail="Error de integridad de datos: " + str(e.orig)
        )
    except SQLAlchemyError as e:
        await db.rollback()
        logger.error("[update_country] Error SQLAlchemy: %s", e, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Error en la base de datos"
        )
    except Exception as e:
        await db.rollback()
        logger.exception("[update_country] Error inesperado", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error interno: {str(e)}"
        )
        
async def patch_country(
    db: AsyncSession,
    country_id: UUID,
    country_in: 'CountryPatch',
    user_id: UUID  # ¡Para log de auditoría!
) -> tuple:
    """
    Actualiza parcialmente una país (PATCH) y registra log de auditoría.
    Retorna (country_actualizada, log_de_auditoria) o (None, None) si no existe.
    """
    try:
         # 1. Busca la país existente
        result = await db.execute(select(Country).where(Country.id == country_id))
        country = result.scalars().first()
        if not country:
            logger.warning(f"[patch_country] País {country_id} no encontrado.")
            return None, None

        data = country_in.dict(exclude_unset=True)
        cambios = []

        for field, value in data.items():
            if hasattr(country, field):
                old_value = getattr(country, field)
                if old_value != value:
                    cambios.append(f"{field}: '{old_value}' → '{value}'")
                    setattr(country, field, value)

        if not cambios:
            logger.info(f"[patch_country] No hubo cambios en el País {country_id}.")
            return country, None

        country.updated_at = datetime.utcnow()
        audit_level = await get_audit_level(db)    # Decidir si registrar el log según el nivel
        if audit_level >= 1 and user_id:
            log = await log_action(
                db,
                action="PATCH",
                entity="Country",
                entity_id=country.id,
                description=f"Actualización parcial: {', '.join(cambios)}",
                user_id=user_id,
            )

        await db.flush()  # Asegura que los cambios y log estén listos para commit

        logger.info(f"[patch_country] País {country_id} parcheado por el usuario {user_id}. Cambios: {cambios}")
        return country, log

    except IntegrityError as e:
        await db.rollback()
        logger.error("[patch_country] Error de integridad: %s", e, exc_info=True)
        raise HTTPException(
            status_code=400,
            detail="Error de integridad de datos: " + str(e.orig)
        )
    except SQLAlchemyError as e:
        await db.rollback()
        logger.error("[patch_country] Error SQLAlchemy: %s", e, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Error en la base de datos"
        )
    except Exception as e:
        await db.rollback()
        logger.exception("[patch_country] Error inesperado", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error interno: {str(e)}"
        )
