from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from uuid import UUID
from typing import List, Optional

from app.schemas.unit import (
    UnitCreate, UnitUpdate, UnitRead, UnitPatch, UnitImportResult, UnitListResponse
)
from app.crud.unit import (
    create_unit, get_units, get_unit_by_id, update_unit, patch_unit
)
from app.models.user import User
from app.models.unit import Unit
from app.dependencies.current_user import get_current_user
from app.core.security import get_async_db
from app.utils.audit import log_action
import csv
from io import StringIO
from app.utils.audit_level import get_audit_level

import logging
logger = logging.getLogger(__name__)

router = APIRouter(tags=["Units"])
# ==============================
# CREATE - POST
# ==============================
@router.post("/", response_model=UnitRead)
async def create_unit_endpoint(
    unit_in: UnitCreate,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    try:
        new_unit, log = await create_unit(db, unit_in, current_user.id)
        if log:
            db.add(log)
        await db.commit()
        # Opcional: log de éxito solo aquí (no es obligatorio, pero si quieres monitorear puedes dejarlo)
        logger.info(f"Unidad creada exitosamente: {new_unit.id} - {new_unit.name} por usuario {current_user.id}")
        return UnitRead.model_validate(new_unit)
    except IntegrityError as e:
        await db.rollback()
        logger.error("Error de integridad al crear la unidad: %s", e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error de integridad de datos: " + str(e.orig)
        )
    except SQLAlchemyError as e:
        await db.rollback()
        logger.error("Error de SQLAlchemy al crear unidad: %s", e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error en la base de datos"
        )
    except Exception as e:
        await db.rollback()
        logger.exception("Error interno al crear unidad", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno: {str(e)}"
        )

# ==============================
# GET ALL
# ==============================
@router.get("/", response_model=UnitListResponse)
async def list_unidades(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = None,
    active: Optional[bool] = None,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    try:
        result = await get_units(db, skip, limit, search, active, current_user.id)
        await db.commit()
        return result
    except SQLAlchemyError as e:
        await db.rollback()
        logger.error("Error de base de datos al listar unidades: %s", e, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Ocurrió un error en la base de datos al obtener las unidades"
        )
    except Exception as e:
        await db.rollback()
        logger.exception("Error inesperado al listar unidades", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Ocurrió un error al obtener las unidades"
        )

# ==============================
# GET BY ID
# ==============================
@router.get("/{unit_id}", response_model=UnitRead)
async def read_unit(
    unit_id: UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    try:
        unit = await get_unit_by_id(db, unit_id, current_user.id)
        await db.commit()   # Registrar la auditoría si la hubo
        return UnitRead.model_validate(unit)
    except HTTPException as e:
        await db.rollback()
        logger.error("HTTPException al obtener la unidad: %s", e.detail, exc_info=True)
        raise e
    except Exception as e:
        await db.rollback()
        logger.exception("Error inesperado al obtener la unidad por ID", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Ocurrió un error al consultar la unidad"
        )
        
# ==============================
# UPDATE - PUT
# ==============================
@router.put("/{unit_id}", response_model=UnitRead)
async def update_unit_endpoint(
    unit_id: UUID,
    unit_in: UnitUpdate,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    try:
        updated, log = await update_unit(db, unit_id, unit_in, current_user.id)
        if not updated:
            raise HTTPException(status_code=404, detail="Unidad no encontrada")
        if log:
            db.add(log)
        await db.commit()
        await db.refresh(updated)
        return UnitRead.model_validate(updated)
    except IntegrityError as e:
        await db.rollback()
        logger.error("Error de integridad al actualizar la unidad: %s", e, exc_info=True)
        raise HTTPException(
            status_code=400,
            detail="Error de integridad (nombre duplicado u otra restricción)."
        )
    except Exception as e:
        await db.rollback()
        logger.exception("Error inesperado al actualizar la unidad", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error interno: {str(e)}"
        )

# ==============================
# PARTIAL UPDATE - PATCH
# ==============================
@router.patch("/{unit_id}", response_model=UnitRead)
async def patch_unit_endpoint(
    unit_id: UUID,
    unit_in: UnitPatch,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    try:
        updated, log = await patch_unit(db, unit_id, unit_in, current_user.id)
        if not updated:
            logger.warning(f"[patch_unit_endpoint] Unidad {unit_id} no encontrada.")
            raise HTTPException(status_code=404, detail="Unidad no encontrada")
        if log:
            db.add(log)
        await db.commit()
        await db.refresh(updated)
        logger.info(f"[patch_unit_endpoint] Unidad {unit_id} actualizada parcialmente correctamente.")
        return UnitRead.model_validate(updated)
    except IntegrityError as e:
        await db.rollback()
        logger.error("Error de integridad al actualizar la unidad (PATCH): %s", e, exc_info=True)
        raise HTTPException(
            status_code=400,
            detail="Error de integridad (nombre duplicado u otra restricción)."
        )
    except HTTPException as e:
        await db.rollback()
        logger.error("HTTPException en patch_unit_endpoint: %s", e.detail, exc_info=True)
        raise e
    except Exception as e:
        await db.rollback()
        logger.exception("Error inesperado al actualizar unidad (PATCH)", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error interno: {str(e)}"
        )

# ==============================
# IMPORT MASSIVE BRANDS
# ==============================
@router.post("/import", status_code=201)
async def import_unidades(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    try:
        content = await file.read()
        csv_reader = csv.DictReader(StringIO(content.decode("utf-8")))
        if csv_reader.fieldnames:
            csv_reader.fieldnames = [h.strip().replace('\ufeff', '') for h in csv_reader.fieldnames]
            logger.info(f"Headers después de limpieza: {csv_reader.fieldnames}")
        unidades = []
        user_id = current_user.id
        count = 0
        for row in csv_reader:
            try:
                unit = Unit(
                    name=row["name"],
                    description=row.get("description", ""),
                    symbol=row["symbol"],
                    active=row.get("active", "true").lower() in ("true", "1", "yes", "si"),
                    user_id=current_user.id
                )
                unidades.append(unit)
                count += 1
            except Exception as row_err:
                logger.warning(
                    "Fila con error en importación de unidades (fila %d): %s", count + 1, row_err, exc_info=True
                )
                # Si prefieres abortar la importación ante fila errónea, lanza raise aquí

        if not unidades:
            logger.warning("No se encontraron filas válidas para importar en el archivo CSV.")
            raise HTTPException(
                status_code=400,
                detail="No se encontraron filas válidas para importar."
            )
            
        db.add_all(unidades)        
        audit_level = await get_audit_level(db)    # Decidir si registrar el log según el nivel
        if audit_level > 1 and user_id:        
            await log_action(
                db,
                action="IMPORT",
                entity="Unit",
                description=f"Importación masiva: {len(unidades)} unidades importadas.",
                user_id=user_id
            )
        await db.commit()
        logger.info("Importación masiva de unidads exitosa. Total importadas: %d", len(unidades))
        return {"ok": True, "imported": len(unidades)}

    except IntegrityError as e:
        await db.rollback()
        logger.error("Error de integridad en importación masiva: %s", e, exc_info=True)
        raise HTTPException(
            status_code=400,
            detail=f"Error de integridad (unidad duplicada): {str(e.orig)}"
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