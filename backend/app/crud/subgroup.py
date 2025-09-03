from sqlalchemy.future import select
from uuid import UUID
from app.models.subgroup import SubGroup
from app.schemas.subgroup import SubGroupCreate, SubGroupUpdate, SubGroupPatch
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
from app.models.group import Group 

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/subgroups", tags=["SubGroups"])

async def create_subgroup(db: AsyncSession, subgroup_in: SubGroupCreate, user_id: UUID):
    try:
        subgroup = SubGroup(**subgroup_in.model_dump(), user_id=user_id)
        db.add(subgroup)
        await db.flush()
    except Exception as e:
        logger.exception("Error al crear la subgrupo")  # Solo errores
        raise
    log = None
    try:
        audit_level = await get_audit_level(db)    # Decidir si registrar el log según el nivel
        if audit_level > 1:
            description = (
                f"Subgrupo creado: {subgroup.name} "
                f"(id={subgroup.id}, description={subgroup.description}, group_id={subgroup.group_id}, active={subgroup.active})"
            )
            log = await log_action(
                db,
                action="CREATE",
                entity="SubGroup",
                entity_id=subgroup.id,
                description=description,
                user_id=subgroup.user_id
            )
    except Exception as e:
        logger.exception("Error al crear el log de auditoría")  # Solo errores
        raise
    print(log)
    return subgroup, log


# GET ALL
async def get_subgroups(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    active: Optional[bool] = None,
    user_id: Optional[UUID] = None,  # Para auditoría
) -> dict:
    """
    Retorna una lista paginada de subcategorías, con soporte para búsqueda por nombre y filtro por estado activo.
    Incluye el nombre de la categoría asociada.
    """
    try:
        # Hacemos JOIN con Group para obtener el nombre
        query = (
            select(SubGroup, Group.name)
            .join(Group, SubGroup.group_id == Group.id)
        )
        if search:
            query = query.where(SubGroup.name.ilike(f"%{search}%"))
        if active is not None:
            query = query.where(SubGroup.active == active)

        # Calcular total de resultados
        total_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(total_query)
        total = total_result.scalar_one()

        # Obtener las subgrupos paginadas con nombre de categoría
        result = await db.execute(
            query.offset(skip).limit(limit).order_by(SubGroup.name)
        )
        rows = result.all()
        # Construimos la lista con el nombre del subgrupo
        subgroups = [
            {
                "id": sg.id,
                "code": sg.code,
                "name": sg.name,
                "group_id": sg.group_id,   # <-- Este campo es obligatorio
                "group_name": group_name,  # Aquí va el nombre
                "description": sg.description,
                "active": sg.active,
                "created_at": sg.created_at,
                "updated_at": sg.updated_at,
                "user_id": sg.user_id,
            }
            for sg, group_name in rows
        ]
        
        audit_level = await get_audit_level(db)
        if audit_level > 2 and user_id:
            await log_action(
                db,
                action="GETALL",
                entity="SubGroup",
                description=f"Consulta de subgrupos - filtros: search='{search}', active={active}, skip={skip}, limit={limit}",
                user_id=user_id,
            )
        return {"total": total, "items": subgroups}
    except SQLAlchemyError as e:
        await db.rollback()
        logging.exception("Error de base de datos en get_subgrupos", exc_info=True)
        raise
    except Exception as e:
        await db.rollback()
        logging.exception("Error inesperado en get_subgrupos", exc_info=True)
        raise  
  
async def get_subgroup_by_id(
    db: AsyncSession,
    subgroup_id: UUID,
    user_id: UUID = None  # Permite auditoría solo si hay user_id
) -> SubGroup:
    """
    Recupera una subgrupo por su UUID y registra auditoría si se encuentra.

    Args:
        db (AsyncSession): Sesión de base de datos asincrónica.
        subgroup_id (UUID): ID de la subgrupo a buscar.
        user_id (UUID, opcional): Usuario que realiza la consulta (para registrar auditoría).

    Returns:
        SubGroup: Objeto encontrado.

    Raises:
        HTTPException:
            - 404 si no se encuentra el subgrupo.
            - 500 si ocurre un error de base de datos.
    """
    try:
        result = await db.execute(select(SubGroup).where(SubGroup.id == subgroup_id))
        subgroup = result.scalars().first()

        if not subgroup:
            logger.warning(f"[GET_BRAND_BY_ID] subgrupo no encontrado: {subgroup_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Subgrupo con ID {subgroup_id} no encontrado"
            )
            
        audit_level = await get_audit_level(db)    # Decidir si registrar el log según el nivel
        if audit_level > 2 and user_id:
            # Registrar auditoría si hay user_id
            if user_id:
                await log_action(
                    db,
                    action="GETID",
                    entity="SubGroup",
                    entity_id=subgroup.id,
                    description=f"Consultó subgrupo: {subgroup.name}",
                    user_id=user_id
                )
            # No commit aquí, solo flush si log_action lo requiere
            db.flush()
        return subgroup

    except SQLAlchemyError as e:
        await db.rollback()
        logger.error(f"[GET_BRAND_BY_ID] Error al consultar subgrupo {subgroup_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al consultar la subgrupo"
        )
    except Exception as e:
        await db.rollback()
        logger.exception(f"[GET_BRAND_BY_ID] Error inesperado al consultar subgrupo {subgroup_id}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ocurrió un error inesperado al consultar la subgrupo"
        )       


# UPDATE (PUT = total)
async def update_subgroup(
    db: AsyncSession,
    subgroup_id: UUID,
    subgroup_in: 'SubGroupUpdate',
    user_id: UUID
):
    """
    Actualiza una subgrupo y construye el log de auditoría.
    - Retorna (subgroup_actualizada, log_de_auditoria)
    - Si no hay cambios, retorna (subgroup, None)
    - Si la subgrupo no existe, retorna (None, None)
    """
    try:
        # 1. Busca el subgrupo existente
        result = await db.execute(select(SubGroup).where(SubGroup.id == subgroup_id))
        subgroup = result.scalars().first()
        if not subgroup:
            logger.info(f"[update_subgroup] subgrupo {subgroup_id} no encontrado.")
            return None, None

        cambios = []
         # 3. Detecta y aplica otros cambios
        if subgroup.code != subgroup_in.code:
            cambios.append(f"code: '{subgroup.code}' → '{subgroup_in.code}'")
            subgroup.code = subgroup_in.code
        # 2. Valida unicidad de nombre SOLO si cambia el nombre
        if subgroup.name != subgroup_in.name:
            existing = await db.execute(
                select(SubGroup).where(SubGroup.name == subgroup_in.name, SubGroup.id != subgroup_id)
            )
            if existing.scalars().first():
                logger.warning(f"[update_subgroup] Nombre duplicado: {subgroup_in.name}")
                raise HTTPException(
                    status_code=400,
                    detail=f"Ya existe una subgrupo con el nombre '{subgroup_in.name}'."
                )
            cambios.append(f"nombre: '{subgroup.name}' → '{subgroup_in.name}'")
            subgroup.name = subgroup_in.name

        # 3. Detecta y aplica otros cambios
        if subgroup.description != subgroup_in.description:
            cambios.append(f"descripción: '{subgroup.description}' → '{subgroup_in.description}'")
            subgroup.description = subgroup_in.description
        if subgroup.group_id != subgroup_in.group_id:
            cambios.append(f"subgrupo: '{subgroup.group_id}' → '{subgroup_in.group_id}'")
            subgroup.group_id = subgroup_in.group_id
        if subgroup.active != subgroup_in.active:
            cambios.append(f"activo: {subgroup.active} → {subgroup_in.active}")
            subgroup.active = subgroup_in.active

        # 4. Si no hay cambios, retorna solo la subgrupo (sin log)
        if not cambios:
            logger.info(f"[update_subgroup] No hubo cambios en el subgrupo {subgroup_id}.")
            return subgroup, None

        # 5. Actualiza el timestamp
        subgroup.updated_at = datetime.utcnow()
        audit_level = await get_audit_level(db)    # Decidir si registrar el log según el nivel
        if audit_level >= 1 and user_id:
            # 6. Crea el log de auditoría con la descripción de cambios
            log = await log_action(
                db,
                action="UPDATE",
                entity="SubGroup",
                entity_id=subgroup.id,
                description=f"Cambios en el subgrupo: {', '.join(cambios)}",
                user_id=user_id,
            )

        await db.flush()  # Asegura que ambos cambios estén en la sesión

        logger.info(f"[update_subgroup] subgrupo {subgroup_id} actualizado por usuario {user_id}.")
        return subgroup, log

    except IntegrityError as e:
        await db.rollback()
        logger.error("[update_subgroup] Error de integridad: %s", e, exc_info=True)
        raise HTTPException(
            status_code=400,
            detail="Error de integridad de datos: " + str(e.orig)
        )
    except SQLAlchemyError as e:
        await db.rollback()
        logger.error("[update_subgroup] Error SQLAlchemy: %s", e, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Error en la base de datos"
        )
    except Exception as e:
        await db.rollback()
        logger.exception("[update_subgroup] Error inesperado", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error interno: {str(e)}"
        )
        
async def patch_subgroup(
    db: AsyncSession,
    subgroup_id: UUID,
    subgroup_in: 'SubGroupPatch',
    user_id: UUID  # ¡Para log de auditoría!
) -> tuple:
    """
    Actualiza parcialmente una subgrupo (PATCH) y registra log de auditoría.
    Retorna (subgroup_actualizada, log_de_auditoria) o (None, None) si no existe.
    """
    try:
         # 1. Busca la subgrupo existente
        result = await db.execute(select(SubGroup).where(SubGroup.id == subgroup_id))
        subgroup = result.scalars().first()
        if not subgroup:
            logger.warning(f"[patch_subgroup] subgrupo {subgroup_id} no encontrado.")
            return None, None

        data = subgroup_in.dict(exclude_unset=True)
        cambios = []

        for field, value in data.items():
            if hasattr(subgroup, field):
                old_value = getattr(subgroup, field)
                if old_value != value:
                    cambios.append(f"{field}: '{old_value}' → '{value}'")
                    setattr(subgroup, field, value)

        if not cambios:
            logger.info(f"[patch_subgroup] No hubo cambios en el subgrupo {subgroup_id}.")
            return subgroup, None

        subgroup.updated_at = datetime.utcnow()
        audit_level = await get_audit_level(db)    # Decidir si registrar el log según el nivel
        if audit_level >= 1 and user_id:
            log = await log_action(
                db,
                action="PATCH",
                entity="SubGroup",
                entity_id=subgroup.id,
                description=f"Actualización parcial: {', '.join(cambios)}",
                user_id=user_id
            )

        await db.flush()  # Asegura que los cambios y log estén listos para commit

        logger.info(f"[patch_subgroup] subgrupo {subgroup_id} parcheada por usuario {user_id}. Cambios: {cambios}")
        return subgroup, log

    except IntegrityError as e:
        await db.rollback()
        logger.error("[patch_subgroup] Error de integridad: %s", e, exc_info=True)
        raise HTTPException(
            status_code=400,
            detail="Error de integridad de datos: " + str(e.orig)
        )
    except SQLAlchemyError as e:
        await db.rollback()
        logger.error("[patch_subgroup] Error SQLAlchemy: %s", e, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Error en la base de datos"
        )
    except Exception as e:
        await db.rollback()
        logger.exception("[patch_subgroup] Error inesperado", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error interno: {str(e)}"
        )
