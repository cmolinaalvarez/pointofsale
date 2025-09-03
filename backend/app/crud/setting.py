from sqlalchemy.future import select
from uuid import UUID
from app.models.setting import Setting
from app.schemas.setting import SettingCreate, SettingUpdate, SettingPatch
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

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/settings", tags=["Settings"])

async def create_setting(db: AsyncSession, setting_in: SettingCreate, user_id: UUID):
    try:
        setting = Setting(**setting_in.model_dump(), user_id=user_id)
        db.add(setting)
        await db.flush()
    except Exception as e:
        logger.exception("Error al crear la marca")  # Solo errores
        raise

    try:
        log = await log_action(
            db,
            action="CREATE",
            entity="Setting",
            entity_id=setting.id,
            description=f"Marca creada: {setting.description}",
            user_id=setting.user_id
        )
    except Exception as e:
        logger.exception("Error al crear el log de auditoría")  # Solo errores
        raise

    return setting, log

# GET ALL

async def get_settings(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    active: Optional[bool] = None,
    user_id: Optional[UUID] = None,  # Para auditoría
) -> dict:
    """
    Retorna una lista paginada de marcas, con soporte para búsqueda por nombre y filtro por estado activo.
    Registra la auditoría si es necesario.
    """
    try:
        query = select(Setting)

        if search:
            query = query.where(Setting.description.ilike(f"%{search}%"))
        if active is not None:
            query = query.where(Setting.active == active)

        # Calcular total de resultados
        total_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(total_query)
        total = total_result.scalar_one()

        # Obtener las marcas paginadas
        result = await db.execute(
            query.offset(skip).limit(limit).order_by(Setting.description)
        )
        settings = result.scalars().all()

        # Registrar la consulta en auditoría (solo si user_id no es None)
        if user_id:
            await log_action(
                db,
                action="GETALL",
                entity="Setting",
                description=f"Consulta de marcas - filtros: search='{search}', active={active}, skip={skip}, limit={limit}",
                user_id=user_id,
            )
            # db.flush()
        return {"total": total, "items": settings}
    except SQLAlchemyError as e:
        await db.rollback()
        logging.exception("Error de base de datos en get_settings", exc_info=True)
        raise  # Puedes relanzar aquí y manejarlo en el endpoint
    except Exception as e:
        await db.rollback()
        logging.exception("Error inesperado en get_settings", exc_info=True)
        raise
  
async def get_setting_by_id(
    db: AsyncSession,
    setting_id: UUID,
    user_id: UUID = None  # Permite auditoría solo si hay user_id
) -> Setting:
    """
    Recupera una marca por su UUID y registra auditoría si se encuentra.

    Args:
        db (AsyncSession): Sesión de base de datos asincrónica.
        setting_id (UUID): ID de la marca a buscar.
        user_id (UUID, opcional): Usuario que realiza la consulta (para registrar auditoría).

    Returns:
        Setting: Objeto encontrado.

    Raises:
        HTTPException:
            - 404 si no se encuentra la marca.
            - 500 si ocurre un error de base de datos.
    """
    try:
        result = await db.execute(select(Setting).where(Setting.id == setting_id))
        setting = result.scalars().first()

        if not setting:
            logger.warning(f"[GET_SETTING_BY_ID] Marca no encontrada: {setting_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Marca con ID {setting_id} no encontrada"
            )
        # Registrar auditoría si hay user_id
        if user_id:
            await log_action(
                db,
                action="GETID",
                entity="Setting",
                entity_id=setting.id,
                description=f"Consultó marca: {setting.description}",
                user_id=user_id
            )
            # No commit aquí, solo flush si log_action lo requiere
            db.flush()
        return setting

    except SQLAlchemyError as e:
        await db.rollback()
        logger.error(f"[GET_SETTING_BY_ID] Error al consultar marca {setting_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al consultar la marca"
        )
    except Exception as e:
        await db.rollback()
        logger.exception(f"[GET_SETTING_BY_ID] Error inesperado al consultar marca {setting_id}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ocurrió un error inesperado al consultar la marca"
        )       


# UPDATE (PUT = total)
async def update_setting(
    db: AsyncSession,
    setting_id: UUID,
    setting_in: 'SettingUpdate',
    user_id: UUID
):
    """
    Actualiza una marca y construye el log de auditoría.
    - Retorna (setting_actualizada, log_de_auditoria)
    - Si no hay cambios, retorna (setting, None)
    - Si la marca no existe, retorna (None, None)
    """
    try:
        # 1. Busca la marca existente
        result = await db.execute(select(Setting).where(Setting.id == setting_id))
        setting = result.scalars().first()
        if not setting:
            logger.info(f"[update_setting] Marca {setting_id} no encontrada.")
            return None, None

        cambios = []

        # 2. Valida unicidad de nombre SOLO si cambia el nombre
        if setting.description != setting_in.description:
            existing = await db.execute(
                select(Setting).where(Setting.description == setting_in.description, Setting.id != setting_id)
            )
            if existing.scalars().first():
                logger.warning(f"[update_setting] Nombre duplicado: {setting_in.description}")
                raise HTTPException(
                    status_code=400,
                    detail=f"Ya existe una marca con el nombre '{setting_in.description}'."
                )
            cambios.append(f"nombre: '{setting.description}' → '{setting_in.description}'")
            setting.description = setting_in.description

        # 3. Detecta y aplica otros cambios
        if setting.description != setting_in.description:
            cambios.append(f"descripción: '{setting.description}' → '{setting_in.description}'")
            setting.description = setting_in.description
        if setting.active != setting_in.active:
            cambios.append(f"activo: {setting.active} → {setting_in.active}")
            setting.active = setting_in.active

        # 4. Si no hay cambios, retorna solo la marca (sin log)
        if not cambios:
            logger.info(f"[update_setting] No hubo cambios en la configuración {setting_id}.")
            return setting, None

        # 5. Actualiza el timestamp
        setting.updated_at = datetime.utcnow()

        # 6. Crea el log de auditoría con la descripción de cambios
        log = await log_action(
            db,
            action="UPDATE",
            entity="Setting",
            entity_id=setting.id,
            description=f"Cambios en la Configuración: {', '.join(cambios)}",
            user_id=user_id,
        )

        await db.flush()  # Asegura que ambos cambios estén en la sesión

        logger.info(f"[update_setting] Marca {setting_id} actualizada por usuario {user_id}.")
        return setting, log

    except IntegrityError as e:
        await db.rollback()
        logger.error("[update_setting] Error de integridad: %s", e, exc_info=True)
        raise HTTPException(
            status_code=400,
            detail="Error de integridad de datos: " + str(e.orig)
        )
    except SQLAlchemyError as e:
        await db.rollback()
        logger.error("[update_setting] Error SQLAlchemy: %s", e, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Error en la base de datos"
        )
    except Exception as e:
        await db.rollback()
        logger.exception("[update_setting] Error inesperado", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error interno: {str(e)}"
        )
        
async def patch_setting(
    db: AsyncSession,
    setting_id: UUID,
    setting_in: 'SettingPatch',
    user_id: UUID  # ¡Para log de auditoría!
) -> tuple:
    """
    Actualiza parcialmente una marca (PATCH) y registra log de auditoría.
    Retorna (setting_actualizada, log_de_auditoria) o (None, None) si no existe.
    """
    try:
        setting = await get_setting_by_id(db, setting_id)
        if not setting:
            logger.warning(f"[patch_setting] Marca {setting_id} no encontrada.")
            return None, None

        data = setting_in.dict(exclude_unset=True)
        cambios = []

        for field, value in data.items():
            if hasattr(setting, field):
                old_value = getattr(setting, field)
                if old_value != value:
                    cambios.append(f"{field}: '{old_value}' → '{value}'")
                    setattr(setting, field, value)

        if not cambios:
            logger.info(f"[patch_setting] No hubo cambios en la configuración {setting_id}.")
            return setting, None

        setting.updated_at = datetime.utcnow()

        log = await log_action(
            db,
            action="PATCH",
            entity="Setting",
            entity_id=setting.id,
            description=f"Actualización parcial: {', '.join(cambios)}",
            user_id=user_id,
        )

        await db.flush()  # Asegura que los cambios y log estén listos para commit

        logger.info(f"[patch_setting] Marca {setting_id} parcheada por usuario {user_id}. Cambios: {cambios}")
        return setting, log

    except IntegrityError as e:
        await db.rollback()
        logger.error("[patch_setting] Error de integridad: %s", e, exc_info=True)
        raise HTTPException(
            status_code=400,
            detail="Error de integridad de datos: " + str(e.orig)
        )
    except SQLAlchemyError as e:
        await db.rollback()
        logger.error("[patch_setting] Error SQLAlchemy: %s", e, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Error en la base de datos"
        )
    except Exception as e:
        await db.rollback()
        logger.exception("[patch_setting] Error inesperado", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error interno: {str(e)}"
        )
