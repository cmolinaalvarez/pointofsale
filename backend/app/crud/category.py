from sqlalchemy.future import select
from uuid import UUID
from app.models.category import Category
from app.schemas.category import CategoryCreate, CategoryUpdate, CategoryPatch
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

router = APIRouter(prefix="/categories", tags=["Categories"])

async def create_category(db: AsyncSession, category_in: CategoryCreate, user_id: UUID):
    try:
        category = Category(**category_in.model_dump(), user_id=user_id)
        db.add(category)
        await db.flush()
    except Exception as e:
        logger.exception("Error al crear la categoría")  # Solo errores
        raise
    log = None
    try:
        description = (
            f"Categoría creada: {category.name} "
            f"(id={category.id}, code={category.code}, description={category.description}, active={category.active})"
        )
        audit_level = await get_audit_level(db)    # Decidir si registrar el log según el nivel
        if audit_level > 1:
            log = await log_action(
                db,
                action="CREATE",
                entity="Category",
                entity_id=category.id,
                description=description,
                user_id=category.user_id
            )
    except Exception as e:
        logger.exception("Error al crear el log de auditoría")  # Solo errores
        raise
    print(log)
    return category, log

# GET ALL

async def get_categories(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    active: Optional[bool] = None,
    user_id: Optional[UUID] = None,  # Para auditoría
) -> dict:
    """
    Retorna una lista paginada de categorías, con soporte para búsqueda por nombre y filtro por estado activo.
    Registra la auditoría si es necesario.
    """
    try:
        query = select(Category)

        if search:
            query = query.where(Category.name.ilike(f"%{search}%"))
        if active is not None:
            query = query.where(Category.active == active)

        # Calcular total de resultados
        total_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(total_query)
        total = total_result.scalar_one()

        # Obtener las categorías paginadas
        result = await db.execute(
            query.offset(skip).limit(limit).order_by(Category.name)
        )
        categorys = result.scalars().all()
        audit_level = await get_audit_level(db)    # Decidir si registrar el log según el nivel
        if audit_level > 2 and user_id:
            await log_action(
                db,
                action="GETALL",
                entity="Category",
                description=f"Consulta de categorías - filtros: search='{search}', active={active}, skip={skip}, limit={limit}",
                user_id=user_id,
            )
            # db.flush()
        return {"total": total, "items": categorys}
    except SQLAlchemyError as e:
        await db.rollback()
        logging.exception("Error de base de datos en get_categorías", exc_info=True)
        raise  # Puedes relanzar aquí y manejarlo en el endpoint
    except Exception as e:
        await db.rollback()
        logging.exception("Error inesperado en get_categorías", exc_info=True)
        raise
  
async def get_category_by_id(
    db: AsyncSession,
    category_id: UUID,
    user_id: UUID = None  # Permite auditoría solo si hay user_id
) -> Category:
    """
    Recupera una categoría por su UUID y registra auditoría si se encuentra.

    Args:
        db (AsyncSession): Sesión de base de datos asincrónica.
        category_id (UUID): ID de la categoría a buscar.
        user_id (UUID, opcional): Usuario que realiza la consulta (para registrar auditoría).

    Returns:
        Category: Objeto encontrado.

    Raises:
        HTTPException:
            - 404 si no se encuentra la categoría.
            - 500 si ocurre un error de base de datos.
    """
    try:
        result = await db.execute(select(Category).where(Category.id == category_id))
        category = result.scalars().first()

        if not category:
            logger.warning(f"[GET_BRAND_BY_ID] Categoría no encontrada: {category_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Categoría con ID {category_id} no encontrada"
            )
            
        audit_level = await get_audit_level(db)    # Decidir si registrar el log según el nivel
        if audit_level > 2 and user_id:
            # Registrar auditoría si hay user_id
            if user_id:
                await log_action(
                    db,
                    action="GETID",
                    entity="Category",
                    entity_id=category.id,
                    description=f"Consultó categoría: {category.name}",
                    user_id=user_id
                )
            # No commit aquí, solo flush si log_action lo requiere
            db.flush()
        return category

    except SQLAlchemyError as e:
        await db.rollback()
        logger.error(f"[GET_BRAND_BY_ID] Error al consultar categoría {category_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al consultar la categoría"
        )
    except Exception as e:
        await db.rollback()
        logger.exception(f"[GET_BRAND_BY_ID] Error inesperado al consultar categoría {category_id}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ocurrió un error inesperado al consultar la categoría"
        )       


# UPDATE (PUT = total)
async def update_category(
    db: AsyncSession,
    category_id: UUID,
    category_in: 'CategoryUpdate',
    user_id: UUID
):
    """
    Actualiza una categoría y construye el log de auditoría.
    - Retorna (category_actualizada, log_de_auditoria)
    - Si no hay cambios, retorna (category, None)
    - Si la categoría no existe, retorna (None, None)
    """
    try:
        # 1. Busca la categoría existente
        result = await db.execute(select(Category).where(Category.id == category_id))
        category = result.scalars().first()
        if not category:
            logger.info(f"[update_category] Categoría {category_id} no encontrada.")
            return None, None

        cambios = []
        
        # 1. Detecta y aplica otros cambios
        if category.code != category_in.code:
            cambios.append(f"código: '{category.code}' → '{category_in.code}'")
            category.code = category_in.code

        # 2. Valida unicidad de nombre SOLO si cambia el nombre
        if category.name != category_in.name:
            existing = await db.execute(
                select(Category).where(Category.name == category_in.name, Category.id != category_id)
            )
            if existing.scalars().first():
                logger.warning(f"[update_category] Nombre duplicado: {category_in.name}")
                raise HTTPException(
                    status_code=400,
                    detail=f"Ya existe una categoría con el nombre '{category_in.name}'."
                )
            cambios.append(f"nombre: '{category.name}' → '{category_in.name}'")
            category.name = category_in.name

        # 3. Detecta y aplica otros cambios
        if category.code != category_in.code:
            cambios.append(f"code: '{category.code}' → '{category_in.code}'")
            category.code = category_in.code
        
            # 3. Detecta y aplica otros cambios
        if category.description != category_in.description:
            cambios.append(f"code: '{category.description}' → '{category_in.description}'")
            category.description = category_in.description
        
        if category.active != category_in.active:
            cambios.append(f"activo: {category.active} → {category_in.active}")
            category.active = category_in.active

        # 4. Si no hay cambios, retorna solo la categoría (sin log)
        if not cambios:
            logger.info(f"[update_category] No hubo cambios en la categoría {category_id}.")
            return category, None

        # 5. Actualiza el timestamp
        category.updated_at = datetime.utcnow()
        audit_level = await get_audit_level(db)    # Decidir si registrar el log según el nivel
        if audit_level >= 1 and user_id:
            # 6. Crea el log de auditoría con la descripción de cambios
            log = await log_action(
                db,
                action="UPDATE",
                entity="Category",
                entity_id=category.id,
                description=f"Cambios en la Categoría: {', '.join(cambios)}",
                user_id=user_id,
            )

        await db.flush()  # Asegura que ambos cambios estén en la sesión

        logger.info(f"[update_category] Categoría {category_id} actualizada por usuario {user_id}.")
        return category, log

    except IntegrityError as e:
        await db.rollback()
        logger.error("[update_category] Error de integridad: %s", e, exc_info=True)
        raise HTTPException(
            status_code=400,
            detail="Error de integridad de datos: " + str(e.orig)
        )
    except SQLAlchemyError as e:
        await db.rollback()
        logger.error("[update_category] Error SQLAlchemy: %s", e, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Error en la base de datos"
        )
    except Exception as e:
        await db.rollback()
        logger.exception("[update_category] Error inesperado", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error interno: {str(e)}"
        )
        
async def patch_category(
    db: AsyncSession,
    category_id: UUID,
    category_in: 'CategoryPatch',
    user_id: UUID  # ¡Para log de auditoría!
) -> tuple:
    """
    Actualiza parcialmente una categoría (PATCH) y registra log de auditoría.
    Retorna (category_actualizada, log_de_auditoria) o (None, None) si no existe.
    """
    try:
         # 1. Busca la categoría existente
        result = await db.execute(select(Category).where(Category.id == category_id))
        category = result.scalars().first()
        if not category:
            logger.warning(f"[patch_category] Marca {category_id} no encontrada.")
            return None, None

        data = category_in.dict(exclude_unset=True)
        cambios = []

        for field, value in data.items():
            if hasattr(category, field):
                old_value = getattr(category, field)
                if old_value != value:
                    cambios.append(f"{field}: '{old_value}' → '{value}'")
                    setattr(category, field, value)

        if not cambios:
            logger.info(f"[patch_category] No hubo cambios en la categoría {category_id}.")
            return category, None

        category.updated_at = datetime.utcnow()
        audit_level = await get_audit_level(db)    # Decidir si registrar el log según el nivel
        if audit_level >= 1 and user_id:
            log = await log_action(
                db,
                action="PATCH",
                entity="Category",
                entity_id=category.id,
                description=f"Actualización parcial: {', '.join(cambios)}",
                user_id=user_id,
            )

        await db.flush()  # Asegura que los cambios y log estén listos para commit

        logger.info(f"[patch_category] Categoría {category_id} parcheada por usuario {user_id}. Cambios: {cambios}")
        return category, log

    except IntegrityError as e:
        await db.rollback()
        logger.error("[patch_category] Error de integridad: %s", e, exc_info=True)
        raise HTTPException(
            status_code=400,
            detail="Error de integridad de datos: " + str(e.orig)
        )
    except SQLAlchemyError as e:
        await db.rollback()
        logger.error("[patch_category] Error SQLAlchemy: %s", e, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Error en la base de datos"
        )
    except Exception as e:
        await db.rollback()
        logger.exception("[patch_category] Error inesperado", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error interno: {str(e)}"
        )
