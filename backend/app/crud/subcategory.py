from sqlalchemy.future import select
from uuid import UUID
from app.models.subcategory import SubCategory
from app.schemas.subcategory import SubCategoryCreate, SubCategoryUpdate, SubCategoryPatch
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
from app.models.category import Category 

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/subcategories", tags=["SubCategories"])

async def create_subcategory(db: AsyncSession, subcategory_in: SubCategoryCreate, user_id: UUID):
    try:
        subcategory = SubCategory(**subcategory_in.model_dump(), user_id=user_id)
        db.add(subcategory)
        await db.flush()
    except Exception as e:
        logger.exception("Error al crear la subcategoría")  # Solo errores
        raise
    log = None
    try:
        audit_level = await get_audit_level(db)    # Decidir si registrar el log según el nivel
        if audit_level > 1:
            description = (
                f"Subcategoría creada: {subcategory.name} "
                f"(id={subcategory.id}, description={subcategory.description}, category_id={subcategory.category_id}, active={subcategory.active})"
            )
            log = await log_action(
                db,
                action="CREATE",
                entity="SubCategory",
                entity_id=subcategory.id,
                description=description,
                user_id=subcategory.user_id
            )
    except Exception as e:
        logger.exception("Error al crear el log de auditoría")  # Solo errores
        raise
    print(log)
    return subcategory, log


# GET ALL
async def get_subcategories(
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
        # Hacemos JOIN con Category para obtener el nombre
        query = (
            select(SubCategory, Category.name)
            .join(Category, SubCategory.category_id == Category.id)
        )

        if search:
            query = query.where(SubCategory.name.ilike(f"%{search}%"))
        if active is not None:
            query = query.where(SubCategory.active == active)

        # Calcular total de resultados
        total_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(total_query)
        total = total_result.scalar_one()

        # Obtener las subcategorías paginadas con nombre de categoría
        result = await db.execute(
            query.offset(skip).limit(limit).order_by(SubCategory.name)
        )
        rows = result.all()
        # Construimos la lista con el nombre de la categoría
        subcategories = [
            {
                "id": sc.id,
                "code": sc.code,
                "name": sc.name,
                "category_id": sc.category_id,   # <-- Este campo es obligatorio
                "category_name": category_name,  # Aquí va el nombre
                "description": sc.description,
                "active": sc.active,
                "created_at": sc.created_at,
                "updated_at": sc.updated_at,
                "user_id": sc.user_id,
            }
            for sc, category_name in rows
        ]
        
        audit_level = await get_audit_level(db)
        if audit_level > 2 and user_id:
            await log_action(
                db,
                action="GETALL",
                entity="SubCategory",
                description=f"Consulta de subcategorías - filtros: search='{search}', active={active}, skip={skip}, limit={limit}",
                user_id=user_id,
            )
        return {"total": total, "items": subcategories}
    except SQLAlchemyError as e:
        await db.rollback()
        logging.exception("Error de base de datos en get_subcategorías", exc_info=True)
        raise
    except Exception as e:
        await db.rollback()
        logging.exception("Error inesperado en get_subcategorías", exc_info=True)
        raise  
    
async def get_subcategory_by_id(
    db: AsyncSession,
    subcategory_id: UUID,
    user_id: UUID = None  # Permite auditoría solo si hay user_id
) -> SubCategory:
    """
    Recupera una subcategoría por su UUID y registra auditoría si se encuentra.

    Args:
        db (AsyncSession): Sesión de base de datos asincrónica.
        subcategory_id (UUID): ID de la subcategoría a buscar.
        user_id (UUID, opcional): Usuario que realiza la consulta (para registrar auditoría).

    Returns:
        SubCategory: Objeto encontrado.

    Raises:
        HTTPException:
            - 404 si no se encuentra la subcategoría.
            - 500 si ocurre un error de base de datos.
    """
    try:
        result = await db.execute(select(SubCategory).where(SubCategory.id == subcategory_id))
        subcategory = result.scalars().first()

        if not subcategory:
            logger.warning(f"[GET_BRAND_BY_ID] Subcategoría no encontrada: {subcategory_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Subcategoría con ID {subcategory_id} no encontrada"
            )
            
        audit_level = await get_audit_level(db)    # Decidir si registrar el log según el nivel
        if audit_level > 2 and user_id:
            # Registrar auditoría si hay user_id
            if user_id:
                await log_action(
                    db,
                    action="GETID",
                    entity="SubCategory",
                    entity_id=subcategory.id,
                    description=f"Consultó subcategoría: {subcategory.name}",
                    user_id=user_id
                )
            # No commit aquí, solo flush si log_action lo requiere
            db.flush()
        return subcategory

    except SQLAlchemyError as e:
        await db.rollback()
        logger.error(f"[GET_BRAND_BY_ID] Error al consultar subcategoría {subcategory_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al consultar la subcategoría"
        )
    except Exception as e:
        await db.rollback()
        logger.exception(f"[GET_BRAND_BY_ID] Error inesperado al consultar subcategoría {subcategory_id}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ocurrió un error inesperado al consultar la subcategoría"
        )       


# UPDATE (PUT = total)
async def update_subcategory(
    db: AsyncSession,
    subcategory_id: UUID,
    subcategory_in: 'SubCategoryUpdate',
    user_id: UUID
):
    """
    Actualiza una subcategoría y construye el log de auditoría.
    - Retorna (subcategory_actualizada, log_de_auditoria)
    - Si no hay cambios, retorna (subcategory, None)
    - Si la subcategoría no existe, retorna (None, None)
    """
    try:
        # 1. Busca la subcategoría existente
        result = await db.execute(select(SubCategory).where(SubCategory.id == subcategory_id))
        subcategory = result.scalars().first()
        if not subcategory:
            logger.info(f"[update_subcategory] Subcategoría {subcategory_id} no encontrada.")
            return None, None

        cambios = []
        
        # 1. Detecta y aplica otros cambios
        if subcategory.code != subcategory_in.code:
            cambios.append(f"código: '{subcategory.code}' → '{subcategory_in.code}'")
            subcategory.code = subcategory_in.code

        # 2. Valida unicidad de nombre SOLO si cambia el nombre
        if subcategory.name != subcategory_in.name:
            existing = await db.execute(
                select(SubCategory).where(SubCategory.name == subcategory_in.name, SubCategory.id != subcategory_id)
            )
            if existing.scalars().first():
                logger.warning(f"[update_subcategory] Nombre duplicado: {subcategory_in.name}")
                raise HTTPException(
                    status_code=400,
                    detail=f"Ya existe una subcategoría con el nombre '{subcategory_in.name}'."
                )
            cambios.append(f"nombre: '{subcategory.name}' → '{subcategory_in.name}'")
            subcategory.name = subcategory_in.name

        # 3. Detecta y aplica otros cambios
        if subcategory.description != subcategory_in.description:
            cambios.append(f"descripción: '{subcategory.description}' → '{subcategory_in.description}'")
            subcategory.description = subcategory_in.description
        if subcategory.category_id != subcategory_in.category_id:
            cambios.append(f"categoría: '{subcategory.category_id}' → '{subcategory_in.category_id}'")
            subcategory.category_id = subcategory_in.category_id
        if subcategory.active != subcategory_in.active:
            cambios.append(f"activo: {subcategory.active} → {subcategory_in.active}")
            subcategory.active = subcategory_in.active

        # 4. Si no hay cambios, retorna solo la subcategoría (sin log)
        if not cambios:
            logger.info(f"[update_subcategory] No hubo cambios en la subcategoría {subcategory_id}.")
            return subcategory, None

        # 5. Actualiza el timestamp
        subcategory.updated_at = datetime.utcnow()
        audit_level = await get_audit_level(db)    # Decidir si registrar el log según el nivel
        if audit_level >= 1 and user_id:
            # 6. Crea el log de auditoría con la descripción de cambios
            log = await log_action(
                db,
                action="UPDATE",
                entity="SubCategory",
                entity_id=subcategory.id,
                description=f"Cambios a la Subcategoría: {', '.join(cambios)}",
                user_id=user_id,
            )

        await db.flush()  # Asegura que ambos cambios estén en la sesión

        logger.info(f"[update_subcategory] Subcategoría {subcategory_id} actualizada por usuario {user_id}.")
        return subcategory, log

    except IntegrityError as e:
        await db.rollback()
        logger.error("[update_subcategory] Error de integridad: %s", e, exc_info=True)
        raise HTTPException(
            status_code=400,
            detail="Error de integridad de datos: " + str(e.orig)
        )
    except SQLAlchemyError as e:
        await db.rollback()
        logger.error("[update_subcategory] Error SQLAlchemy: %s", e, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Error en la base de datos"
        )
    except Exception as e:
        await db.rollback()
        logger.exception("[update_subcategory] Error inesperado", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error interno: {str(e)}"
        )
        
async def patch_subcategory(
    db: AsyncSession,
    subcategory_id: UUID,
    subcategory_in: 'SubCategoryPatch',
    user_id: UUID  # ¡Para log de auditoría!
) -> tuple:
    """
    Actualiza parcialmente una subcategoría (PATCH) y registra log de auditoría.
    Retorna (subcategory_actualizada, log_de_auditoria) o (None, None) si no existe.
    """
    try:
         # 1. Busca la subcategoría existente
        result = await db.execute(select(SubCategory).where(SubCategory.id == subcategory_id))
        subcategory = result.scalars().first()
        if not subcategory:
            logger.warning(f"[patch_subcategory] Subcategoría {subcategory_id} no encontrada.")
            return None, None

        data = subcategory_in.dict(exclude_unset=True)
        cambios = []

        for field, value in data.items():
            if hasattr(subcategory, field):
                old_value = getattr(subcategory, field)
                if old_value != value:
                    cambios.append(f"{field}: '{old_value}' → '{value}'")
                    setattr(subcategory, field, value)

        if not cambios:
            logger.info(f"[patch_subcategory] No hubo cambios en la subcategoría {subcategory_id}.")
            return subcategory, None

        subcategory.updated_at = datetime.utcnow()
        audit_level = await get_audit_level(db)    # Decidir si registrar el log según el nivel
        if audit_level >= 1 and user_id:
            log = await log_action(
                db,
                action="PATCH",
                entity="SubCategory",
                entity_id=subcategory.id,
                description=f"Actualización parcial: {', '.join(cambios)}",
                user_id=user_id,
            )

        await db.flush()  # Asegura que los cambios y log estén listos para commit

        logger.info(f"[patch_subcategory] Subcategoría {subcategory_id} parcheada por usuario {user_id}. Cambios: {cambios}")
        return subcategory, log

    except IntegrityError as e:
        await db.rollback()
        logger.error("[patch_subcategory] Error de integridad: %s", e, exc_info=True)
        raise HTTPException(
            status_code=400,
            detail="Error de integridad de datos: " + str(e.orig)
        )
    except SQLAlchemyError as e:
        await db.rollback()
        logger.error("[patch_subcategory] Error SQLAlchemy: %s", e, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Error en la base de datos"
        )
    except Exception as e:
        await db.rollback()
        logger.exception("[patch_subcategory] Error inesperado", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error interno: {str(e)}"
        )
