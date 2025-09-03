from sqlalchemy.future import select
from uuid import UUID
from app.models.group import Group
from app.schemas.group import GroupCreate, GroupUpdate, GroupPatch
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
from app.models.subcategory import SubCategory 

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/groups", tags=["Groups"])

async def create_group(db: AsyncSession, group_in: GroupCreate, user_id: UUID):
    try:
        group = Group(**group_in.model_dump(), user_id=user_id)
        db.add(group)
        await db.flush()
    except Exception as e:
        logger.exception("Error al crear la grupo")  # Solo errores
        raise
    log = None
    try:
        audit_level = await get_audit_level(db)    # Decidir si registrar el log según el nivel
        if audit_level > 1:
            description = (
                f"Grupo creado: {group.name} "
                f"(id={group.id}, description={group.description}, subcategory_id={group.subcategory_id}, active={group.active})"
            )
            log = await log_action(
                db,
                action="CREATE",
                entity="Group",
                entity_id=group.id,
                description=description,
                user_id=group.user_id
            )
    except Exception as e:
        logger.exception("Error al crear el log de auditoría")  # Solo errores
        raise
    print(log)
    return group, log

# GET ALL
async def get_groups(
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
        # Hacemos JOIN con SubCategory para obtener el nombre
        query = (
            select(Group, SubCategory.name)
            .join(SubCategory, Group.subcategory_id == SubCategory.id)
        )

        if search:
            query = query.where(Group.name.ilike(f"%{search}%"))
        if active is not None:
            query = query.where(Group.active == active)

        # Calcular total de resultados
        total_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(total_query)
        total = total_result.scalar_one()

        # Obtener las subcategorías paginadas con nombre de categoría
        result = await db.execute(
            query.offset(skip).limit(limit).order_by(Group.name)
        )
        rows = result.all()
        # Construimos la lista con el nombre de la categoría
        groups = [
            {
                "id": g.id,
                "code": g.code,
                "name": g.name,
                "subcategory_id": g.subcategory_id,   # <-- Este campo es obligatorio
                "subcategory_name": subcategory_name,  # Aquí va el nombre
                "description": g.description,
                "active": g.active,
                "created_at": g.created_at,
                "updated_at": g.updated_at,
                "user_id": g.user_id,
            }
            for g, subcategory_name in rows
        ]
        
        audit_level = await get_audit_level(db)
        if audit_level > 2 and user_id:
            await log_action(
                db,
                action="GETALL",
                entity="Group",
                description=f"Consulta de subcategorías - filtros: search='{search}', active={active}, skip={skip}, limit={limit}",
                user_id=user_id,
            )
        return {"total": total, "items": groups}
    except SQLAlchemyError as e:
        await db.rollback()
        logging.exception("Error de base de datos en get_subcategorías", exc_info=True)
        raise
    except Exception as e:
        await db.rollback()
        logging.exception("Error inesperado en get_subcategorías", exc_info=True)
        raise  
  
async def get_group_by_id(
    db: AsyncSession,
    group_id: UUID,
    user_id: UUID = None  # Permite auditoría solo si hay user_id
) -> Group:
    """
    Recupera una grupo por su UUID y registra auditoría si se encuentra.

    Args:
        db (AsyncSession): Sesión de base de datos asincrónica.
        group_id (UUID): ID de la grupo a buscar.
        user_id (UUID, opcional): Usuario que realiza la consulta (para registrar auditoría).

    Returns:
        Group: Objeto encontrado.

    Raises:
        HTTPException:
            - 404 si no se encuentra la grupo.
            - 500 si ocurre un error de base de datos.
    """
    try:
        result = await db.execute(select(Group).where(Group.id == group_id))
        group = result.scalars().first()

        if not group:
            logger.warning(f"[GET_BRAND_BY_ID] Grupo no encontrado: {group_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Grupo con ID {group_id} no encontrado"
            )
            
        audit_level = await get_audit_level(db)    # Decidir si registrar el log según el nivel
        if audit_level > 2 and user_id:
            # Registrar auditoría si hay user_id
            if user_id:
                await log_action(
                    db,
                    action="GETID",
                    entity="Group",
                    entity_id=group.id,
                    description=f"Consultó grupo: {group.name}",
                    user_id=user_id
                )
            # No commit aquí, solo flush si log_action lo requiere
            db.flush()
        return group

    except SQLAlchemyError as e:
        await db.rollback()
        logger.error(f"[GET_BRAND_BY_ID] Error al consultar grupo {group_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al consultar la grupo"
        )
    except Exception as e:
        await db.rollback()
        logger.exception(f"[GET_BRAND_BY_ID] Error inesperado al consultar grupo {group_id}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ocurrió un error inesperado al consultar la grupo"
        )       


# UPDATE (PUT = total)
async def update_group(
    db: AsyncSession,
    group_id: UUID,
    group_in: 'GroupUpdate',
    user_id: UUID
):
    """
    Actualiza una grupo y construye el log de auditoría.
    - Retorna (group_actualizada, log_de_auditoria)
    - Si no hay cambios, retorna (group, None)
    - Si la grupo no existe, retorna (None, None)
    """
    try:
        # 1. Busca el grupo existente
        result = await db.execute(select(Group).where(Group.id == group_id))
        group = result.scalars().first()
        if not group:
            logger.info(f"[update_group] Grupo {group_id} no encontrado.")
            return None, None

        cambios = []
         # 3. Detecta y aplica otros cambios
        if group.code != group_in.code:
            cambios.append(f"code: '{group.code}' → '{group_in.code}'")
            group.code = group_in.code
        # 2. Valida unicidad de nombre SOLO si cambia el nombre
        if group.name != group_in.name:
            existing = await db.execute(
                select(Group).where(Group.name == group_in.name, Group.id != group_id)
            )
            if existing.scalars().first():
                logger.warning(f"[update_group] Nombre duplicado: {group_in.name}")
                raise HTTPException(
                    status_code=400,
                    detail=f"Ya existe una grupo con el nombre '{group_in.name}'."
                )
            cambios.append(f"nombre: '{group.name}' → '{group_in.name}'")
            group.name = group_in.name

        # 3. Detecta y aplica otros cambios
        if group.description != group_in.description:
            cambios.append(f"descripción: '{group.description}' → '{group_in.description}'")
            group.description = group_in.description
        if group.subcategory_id != group_in.subcategory_id:
            cambios.append(f"grupo: '{group.subcategory_id}' → '{group_in.subcategory_id}'")
            group.subcategory_id = group_in.subcategory_id
        if group.active != group_in.active:
            cambios.append(f"activo: {group.active} → {group_in.active}")
            group.active = group_in.active

        # 4. Si no hay cambios, retorna solo la grupo (sin log)
        if not cambios:
            logger.info(f"[update_group] No hubo cambios en el grupo {group_id}.")
            return group, None

        # 5. Actualiza el timestamp
        group.updated_at = datetime.utcnow()
        audit_level = await get_audit_level(db)    # Decidir si registrar el log según el nivel
        if audit_level >= 1 and user_id:
            # 6. Crea el log de auditoría con la descripción de cambios
            log = await log_action(
                db,
                action="UPDATE",
                entity="Group",
                entity_id=group.id,
                description=f"Cambios en el Grupo: {', '.join(cambios)}",
                user_id=user_id,
            )

        await db.flush()  # Asegura que ambos cambios estén en la sesión

        logger.info(f"[update_group] Grupo {group_id} actualizado por usuario {user_id}.")
        return group, log

    except IntegrityError as e:
        await db.rollback()
        logger.error("[update_group] Error de integridad: %s", e, exc_info=True)
        raise HTTPException(
            status_code=400,
            detail="Error de integridad de datos: " + str(e.orig)
        )
    except SQLAlchemyError as e:
        await db.rollback()
        logger.error("[update_group] Error SQLAlchemy: %s", e, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Error en la base de datos"
        )
    except Exception as e:
        await db.rollback()
        logger.exception("[update_group] Error inesperado", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error interno: {str(e)}"
        )
        
async def patch_group(
    db: AsyncSession,
    group_id: UUID,
    group_in: 'GroupPatch',
    user_id: UUID  # ¡Para log de auditoría!
) -> tuple:
    """
    Actualiza parcialmente una grupo (PATCH) y registra log de auditoría.
    Retorna (group_actualizada, log_de_auditoria) o (None, None) si no existe.
    """
    try:
         # 1. Busca la grupo existente
        result = await db.execute(select(Group).where(Group.id == group_id))
        group = result.scalars().first()
        if not group:
            logger.warning(f"[patch_group] Grupo {group_id} no encontrado.")
            return None, None

        data = group_in.dict(exclude_unset=True)
        cambios = []

        for field, value in data.items():
            if hasattr(group, field):
                old_value = getattr(group, field)
                if old_value != value:
                    cambios.append(f"{field}: '{old_value}' → '{value}'")
                    setattr(group, field, value)

        if not cambios:
            logger.info(f"[patch_group] No hubo cambios en el grupo {group_id}.")
            return group, None

        group.updated_at = datetime.utcnow()
        audit_level = await get_audit_level(db)    # Decidir si registrar el log según el nivel
        if audit_level >= 1 and user_id:
            log = await log_action(
                db,
                action="PATCH",
                entity="Group",
                entity_id=group.id,
                description=f"Actualización parcial: {', '.join(cambios)}",
                user_id=user_id
            )

        await db.flush()  # Asegura que los cambios y log estén listos para commit

        logger.info(f"[patch_group] Grupo {group_id} parcheada por usuario {user_id}. Cambios: {cambios}")
        return group, log

    except IntegrityError as e:
        await db.rollback()
        logger.error("[patch_group] Error de integridad: %s", e, exc_info=True)
        raise HTTPException(
            status_code=400,
            detail="Error de integridad de datos: " + str(e.orig)
        )
    except SQLAlchemyError as e:
        await db.rollback()
        logger.error("[patch_group] Error SQLAlchemy: %s", e, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Error en la base de datos"
        )
    except Exception as e:
        await db.rollback()
        logger.exception("[patch_group] Error inesperado", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error interno: {str(e)}"
        )
