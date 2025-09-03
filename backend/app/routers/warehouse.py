from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from uuid import UUID
from typing import List, Optional

from app.schemas.warehouse import (
    WarehouseCreate, WarehouseUpdate, WarehouseRead, WarehousePatch, WarehouseImportResult, WarehouseListResponse
)
from app.crud.warehouse import (
    create_warehouse, get_warehouses, get_warehouse_by_id, update_warehouse, patch_warehouse
)
from app.models.user import User
from app.models.warehouse import Warehouse
from app.core.security import get_async_db
from app.utils.audit import log_action
import csv
from io import StringIO
from app.utils.audit_level import get_audit_level
from backend.app.dependencies.auth import get_current_user, require_scopes, current_user_id

import logging
logger = logging.getLogger(__name__)

router = APIRouter(tags=["Warehouses"], dependencies=[Depends(get_current_user)])
# ==============================
# CREATE - POST
# ==============================
@router.post("/", response_model=WarehouseRead)
async def create_warehouse_endpoint(
    warehouse_in: WarehouseCreate,
    db: AsyncSession = Depends(get_async_db),
    uid: str = Depends(current_user_id),
):
    try:
        new_warehouse, log = await create_warehouse(db, warehouse_in, uid)
        if log:
            db.add(log)
        await db.commit()
        # Opcional: log de éxito solo aquí (no es obligatorio, pero si quieres monitorear puedes dejarlo)
        logger.info(f"Bodega creada exitosamente: {new_warehouse.id} - {new_warehouse.name} por usuario {uid}")
        return WarehouseRead.model_validate(new_warehouse)
    except IntegrityError as e:
        await db.rollback()
        logger.error("Error de integridad al crear la bodega: %s", e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error de integridad de datos: " + str(e.orig)
        )
    except SQLAlchemyError as e:
        await db.rollback()
        logger.error("Error de SQLAlchemy al crear bodega: %s", e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error en la base de datos"
        )
    except Exception as e:
        await db.rollback()
        logger.exception("Error interno al crear bodega", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno: {str(e)}"
        )

# ==============================
# GET ALL
# ==============================
@router.get("/", response_model=WarehouseListResponse)
async def list_warehouses(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = None,
    active: Optional[bool] = None,
    db: AsyncSession = Depends(get_async_db),
    uid: str = Depends(current_user_id),
):
    try:
        result = await get_warehouses(db, skip, limit, search, active, uid)
        await db.commit()
        return result
    except SQLAlchemyError as e:
        await db.rollback()
        logger.error("Error de base de datos al listarbodegas: %s", e, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Ocurrió un error en la base de datos al obtener lasbodegas"
        )
    except Exception as e:
        await db.rollback()
        logger.exception("Error inesperado al listarbodegas", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Ocurrió un error al obtener lasbodegas"
        )

# ==============================
# GET BY ID
# ==============================
@router.get("/{warehouse_id}", response_model=WarehouseRead)
async def read_warehouse(
    warehouse_id: UUID,
    db: AsyncSession = Depends(get_async_db),
    uid: str = Depends(current_user_id),
):
    try:
        warehouse = await get_warehouse_by_id(db, warehouse_id, uid)
        await db.commit()   # Registrar la auditoría si la hubo
        return WarehouseRead.model_validate(warehouse)
    except HTTPException as e:
        await db.rollback()
        logger.error("HTTPException al obtener la bodega: %s", e.detail, exc_info=True)
        raise e
    except Exception as e:
        await db.rollback()
        logger.exception("Error inesperado al obtener la bodega por ID", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Ocurrió un error al consultar la bodega"
        )
        
# ==============================
# UPDATE - PUT
# ==============================
@router.put("/{warehouse_id}", response_model=WarehouseRead)
async def update_warehouse_endpoint(
    warehouse_id: UUID,
    warehouse_in: WarehouseUpdate,
    db: AsyncSession = Depends(get_async_db),
    uid: str = Depends(current_user_id),
):
    try:
        updated, log = await update_warehouse(db, warehouse_id, warehouse_in, uid)
        if not updated:
            raise HTTPException(status_code=404, detail="Bodega no encontrada")
        if log:
            db.add(log)
        await db.commit()
        await db.refresh(updated)
        return WarehouseRead.model_validate(updated)
    except IntegrityError as e:
        await db.rollback()
        logger.error("Error de integridad al actualizar bodega: %s", e, exc_info=True)
        raise HTTPException(
            status_code=400,
            detail="Error de integridad (nombre duplicado u otra restricción)."
        )
    except Exception as e:
        await db.rollback()
        logger.exception("Error inesperado al actualizar bodega", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error interno: {str(e)}"
        )

# ==============================
# PARTIAL UPDATE - PATCH
# ==============================
@router.patch("/{warehouse_id}", response_model=WarehouseRead)
async def patch_warehouse_endpoint(
    warehouse_id: UUID,
    warehouse_in: WarehousePatch,
    db: AsyncSession = Depends(get_async_db),
    uid: str = Depends(current_user_id),
):
    try:
        updated, log = await patch_warehouse(db, warehouse_id, warehouse_in, uid)
        if not updated:
            logger.warning(f"[patch_warehouse_endpoint] Bodega {warehouse_id} no encontrada.")
            raise HTTPException(status_code=404, detail="Bodega no encontrada")
        if log:
            db.add(log)
        await db.commit()
        await db.refresh(updated)
        logger.info(f"[patch_warehouse_endpoint] Bodega {warehouse_id} actualizada parcialmente correctamente.")
        return WarehouseRead.model_validate(updated)
    except IntegrityError as e:
        await db.rollback()
        logger.error("Error de integridad al actualizar la bodega (PATCH): %s", e, exc_info=True)
        raise HTTPException(
            status_code=400,
            detail="Error de integridad (nombre duplicado u otra restricción)."
        )
    except HTTPException as e:
        await db.rollback()
        logger.error("HTTPException en patch_warehouse_endpoint: %s", e.detail, exc_info=True)
        raise e
    except Exception as e:
        await db.rollback()
        logger.exception("Error inesperado al actualizar bodega (PATCH)", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error interno: {str(e)}"
        )

# ==============================
# IMPORT MASSIVE BRANDS
# ==============================
@router.post("/import", status_code=201)
async def import_warehouses(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_async_db),
    uid: str = Depends(current_user_id),
):
    try:
        content = await file.read()
        csv_reader = csv.DictReader(StringIO(content.decode("utf-8")))
        if csv_reader.fieldnames:
            csv_reader.fieldnames = [h.strip().replace('\ufeff', '') for h in csv_reader.fieldnames]
            logger.info(f"Headers después de limpieza: {csv_reader.fieldnames}")
        warehouses = []
        user_id = uid
        count = 0
        for row in csv_reader:
            try:
                warehouse = Warehouse(
                    code=row["code"],
                    name=row["name"],
                    description=row.get("description", ""),
                    location=row.get("location"),
                    active=row.get("active", "true").lower() in ("true", "1", "yes", "si"),
                    user_id=uid
                )
                warehouses.append(warehouse)
                count += 1
            except Exception as row_err:
                logger.warning(
                    "Fila con error en importación de bodegas (fila %d): %s", count + 1, row_err, exc_info=True
                )
                # Si prefieres abortar la importación ante fila errónea, lanza raise aquí

        if not warehouses:
            logger.warning("No se encontraron filas válidas para importar en el archivo CSV.")
            raise HTTPException(
                status_code=400,
                detail="No se encontraron filas válidas para importar."
            )
            
        db.add_all(warehouses)        
        audit_level = await get_audit_level(db)    # Decidir si registrar el log según el nivel
        if audit_level > 1 and user_id:        
            await log_action(
                db,
                action="IMPORT",
                entity="Warehouse",
                description=f"Importación masiva: {len(warehouses)} bodegas importadas.",
                user_id=user_id
            )
        await db.commit()
        logger.info("Importación masiva de bodegas exitosa. Total importadas: %d", len(warehouses))
        return {"ok": True, "imported": len(warehouses)}

    except IntegrityError as e:
        await db.rollback()
        logger.error("Error de integridad en importación masiva: %s", e, exc_info=True)
        raise HTTPException(
            status_code=400,
            detail=f"Error de integridad (bodega duplicada): {str(e.orig)}"
        )
    except HTTPException as e:
        await db.rollback()
        logger.error("HTTPException en importación masiva: %s", e.detail, exc_info=True)
        raise e
    except Exception as e:
        await db.rollback()
        logger.exception("Error inesperado en importación masiva", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error interno: {str(e)}"
        )