from sqlalchemy.future import select
from uuid import UUID
from app.models.warehouse import Warehouse
from app.schemas.warehouse import WarehouseCreate, WarehouseUpdate, WarehousePatch
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

router = APIRouter(prefix="/warehouses", tags=["Warehouses"])

async def create_warehouse(db: AsyncSession, warehouse_in: WarehouseCreate, user_id: UUID):
    try:
        warehouse = Warehouse(**warehouse_in.model_dump(), user_id=user_id)
        db.add(warehouse)
        await db.flush()
    except Exception as e:
        logger.exception("Error al crear la bodega")  # Solo errores
        raise
    log = None
    try:
        description = (
            f"Bodega creada: {warehouse.name} "
            f"(id={warehouse.id}, code={warehouse.code}, description={warehouse.description}, location={warehouse.location}, active={warehouse.active})"
        )
        audit_level = await get_audit_level(db)    # Decidir si registrar el log según el nivel
        if audit_level > 1:
            log = await log_action(
                db,
                action="CREATE",
                entity="Warehouse",
                entity_id=warehouse.id,
                description=description,
                user_id=warehouse.user_id
            )
    except Exception as e:
        logger.exception("Error al crear el log de auditoría")  # Solo errores
        raise
    print(log)
    return warehouse, log

# GET ALL

async def get_warehouses(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    active: Optional[bool] = None,
    user_id: Optional[UUID] = None,  # Para auditoría
) -> dict:
    """
    Retorna una lista paginada de bodegas, con soporte para búsqueda por nombre y filtro por estado activo.
    Registra la auditoría si es necesario.
    """
    try:
        query = select(Warehouse)

        if search:
            query = query.where(Warehouse.name.ilike(f"%{search}%"))
        if active is not None:
            query = query.where(Warehouse.active == active)

        # Calcular total de resultados
        total_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(total_query)
        total = total_result.scalar_one()

        # Obtener las bodegas paginadas
        result = await db.execute(
            query.offset(skip).limit(limit).order_by(Warehouse.name)
        )
        warehouses = result.scalars().all()
        audit_level = await get_audit_level(db)    # Decidir si registrar el log según el nivel
        if audit_level > 2 and user_id:
            await log_action(
                db,
                action="GETALL",
                entity="Warehouse",
                description=f"Consulta de bodegas - filtros: search='{search}', active={active}, skip={skip}, limit={limit}",
                user_id=user_id,
            )
            # db.flush()
        return {"total": total, "items": warehouses}
    except SQLAlchemyError as e:
        await db.rollback()
        logging.exception("Error de base de datos en get_warehouses", exc_info=True)
        raise  # Puedes relanzar aquí y manejarlo en el endpoint
    except Exception as e:
        await db.rollback()
        logging.exception("Error inesperado en get_warehouses", exc_info=True)
        raise
  
async def get_warehouse_by_id(
    db: AsyncSession,
    warehouse_id: UUID,
    user_id: UUID = None  # Permite auditoría solo si hay user_id
) -> Warehouse:
    """
    Recupera una bodega por su UUID y registra auditoría si se encuentra.

    Args:
        db (AsyncSession): Sesión de base de datos asincrónica.
        warehouse_id (UUID): ID de la bodega a buscar.
        user_id (UUID, opcional): Usuario que realiza la consulta (para registrar auditoría).

    Returns:
        Warehouse: Objeto encontrado.

    Raises:
        HTTPException:
            - 404 si no se encuentra la bodega.
            - 500 si ocurre un error de base de datos.
    """
    try:
        result = await db.execute(select(Warehouse).where(Warehouse.id == warehouse_id))
        warehouse = result.scalars().first()

        if not warehouse:
            logger.warning(f"[GET_BRAND_BY_ID] Bodega no encontrada: {warehouse_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Bodega con ID {warehouse_id} no encontrada"
            )
            
        audit_level = await get_audit_level(db)    # Decidir si registrar el log según el nivel
        if audit_level > 2 and user_id:
            # Registrar auditoría si hay user_id
            if user_id:
                await log_action(
                    db,
                    action="GETID",
                    entity="Warehouse",
                    entity_id=warehouse.id,
                    description=f"Consultó bodega: {warehouse.name}",
                    user_id=user_id
                )
            # No commit aquí, solo flush si log_action lo requiere
            db.flush()
        return warehouse

    except SQLAlchemyError as e:
        await db.rollback()
        logger.error(f"[GET_BRAND_BY_ID] Error al consultar bodega {warehouse_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al consultar la bodega"
        )
    except Exception as e:
        await db.rollback()
        logger.exception(f"[GET_BRAND_BY_ID] Error inesperado al consultar bodega {warehouse_id}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ocurrió un error inesperado al consultar la bodega"
        )       


# UPDATE (PUT = total)
async def update_warehouse(
    db: AsyncSession,
    warehouse_id: UUID,
    warehouse_in: 'WarehouseUpdate',
    user_id: UUID
):
    """
    Actualiza una bodega y construye el log de auditoría.
    - Retorna (warehouse_actualizada, log_de_auditoria)
    - Si no hay cambios, retorna (warehouse, None)
    - Si la bodega no existe, retorna (None, None)
    """
    try:
        # 1. Busca la bodega existente
        result = await db.execute(select(Warehouse).where(Warehouse.id == warehouse_id))
        warehouse = result.scalars().first()
        if not warehouse:
            logger.info(f"[update_warehouse] Bodega {warehouse_id} no encontrada.")
            return None, None

        cambios = []
        
        # 1. Detecta y aplica otros cambios
        if warehouse.code != warehouse_in.code:
            cambios.append(f"código: '{warehouse.code}' → '{warehouse_in.code}'")
            warehouse.code = warehouse_in.code
       
        # 2. Valida unicidad de nombre SOLO si cambia el nombre
        if warehouse.name != warehouse_in.name:
            existing = await db.execute(
                select(Warehouse).where(Warehouse.name == warehouse_in.name, Warehouse.id != warehouse_id)
            )
            if existing.scalars().first():
                logger.warning(f"[update_warehouse] Nombre duplicado: {warehouse_in.name}")
                raise HTTPException(
                    status_code=400,
                    detail=f"Ya existe una bodega con el nombre '{warehouse_in.name}'."
                )
            cambios.append(f"nombre: '{warehouse.name}' → '{warehouse_in.name}'")
            warehouse.name = warehouse_in.name
            
        # 3. Detecta y aplica otros cambios
        if warehouse.description != warehouse_in.description:
            cambios.append(f"description: '{warehouse.description}' → '{warehouse_in.description}'")
            warehouse.description = warehouse_in.description  
            
             # 3. Detecta y aplica otros cambios
        if warehouse.location != warehouse_in.location:
            cambios.append(f"location: '{warehouse.location}' → '{warehouse_in.location}'")
            warehouse.location = warehouse_in.location              

        if warehouse.active != warehouse_in.active:
            cambios.append(f"activ:e {warehouse.active} → {warehouse_in.active}")
            warehouse.active = warehouse_in.active

        # 4. Si no hay cambios, retorna solo la bodega (sin log)
        if not cambios:
            logger.info(f"[update_warehouse] No hubo cambios en la bodega {warehouse_id}.")
            return warehouse, None

        # 5. Actualiza el timestamp
        warehouse.updated_at = datetime.utcnow()
        audit_level = await get_audit_level(db)    # Decidir si registrar el log según el nivel
        if audit_level >= 1 and user_id:
            # 6. Crea el log de auditoría con la descripción de cambios
            log = await log_action(
                db,
                action="UPDATE",
                entity="Warehouse",
                entity_id=warehouse.id,
                description=f"Cambios en la bodega: {', '.join(cambios)}",
                user_id=user_id,
            )

        await db.flush()  # Asegura que ambos cambios estén en la sesión

        logger.info(f"[update_warehouse] Bodega {warehouse_id} actualizado por usuario {user_id}.")
        return warehouse, log

    except IntegrityError as e:
        await db.rollback()
        logger.error("[update_warehouse] Error de integridad: %s", e, exc_info=True)
        raise HTTPException(
            status_code=400,
            detail="Error de integridad de datos: " + str(e.orig)
        )
    except SQLAlchemyError as e:
        await db.rollback()
        logger.error("[update_warehouse] Error SQLAlchemy: %s", e, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Error en la base de datos"
        )
    except Exception as e:
        await db.rollback()
        logger.exception("[update_warehouse] Error inesperado", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error interno: {str(e)}"
        )
        
async def patch_warehouse(
    db: AsyncSession,
    warehouse_id: UUID,
    warehouse_in: 'WarehousePatch',
    user_id: UUID  # ¡Para log de auditoría!
) -> tuple:
    """
    Actualiza parcialmente un bodega (PATCH) y registra log de auditoría.
    Retorna (warehouse_actualizada, log_de_auditoria) o (None, None) si no existe.
    """
    try:
         # 1. Busca la bodega existente
        result = await db.execute(select(Warehouse).where(Warehouse.id == warehouse_id))
        warehouse = result.scalars().first()
        if not warehouse:
            logger.warning(f"[patch_warehouse] Bodega {warehouse_id} no encontrada.")
            return None, None

        data = warehouse_in.dict(exclude_unset=True)
        cambios = []

        for field, value in data.items():
            if hasattr(warehouse, field):
                old_value = getattr(warehouse, field)
                if old_value != value:
                    cambios.append(f"{field}: '{old_value}' → '{value}'")
                    setattr(warehouse, field, value)

        if not cambios:
            logger.info(f"[patch_warehouse] No hubo cambios en la bodega {warehouse_id}.")
            return warehouse, None

        warehouse.updated_at = datetime.utcnow()
        audit_level = await get_audit_level(db)    # Decidir si registrar el log según el nivel
        if audit_level >= 1 and user_id:
            log = await log_action(
                db,
                action="PATCH",
                entity="Warehouse",
                entity_id=warehouse.id,
                description=f"Actualización parcial: {', '.join(cambios)}",
                user_id=user_id,
            )

        await db.flush()  # Asegura que los cambios y log estén listos para commit

        logger.info(f"[patch_warehouse] Bodega {warehouse_id} parcheada por el usuario {user_id}. Cambios: {cambios}")
        return warehouse, log

    except IntegrityError as e:
        await db.rollback()
        logger.error("[patch_warehouse] Error de integridad: %s", e, exc_info=True)
        raise HTTPException(
            status_code=400,
            detail="Error de integridad de datos: " + str(e.orig)
        )
    except SQLAlchemyError as e:
        await db.rollback()
        logger.error("[patch_warehouse] Error SQLAlchemy: %s", e, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Error en la base de datos"
        )
    except Exception as e:
        await db.rollback()
        logger.exception("[patch_warehouse] Error inesperado", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error interno: {str(e)}"
        )
