from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from uuid import UUID
from typing import List, Optional

from app.schemas.setting import (
    SettingCreate, SettingUpdate, SettingRead, SettingPatch, SettingImportResult, SettingListResponse
)
from app.crud.setting import (
    create_setting, get_settings, get_setting_by_id, update_setting, patch_setting
)
from app.models.user import User
from app.models.setting import Setting
from app.core.security import get_async_db
from app.utils.audit import log_action
from app.utils.audit_level import get_audit_level
from app.dependencies.auth import get_current_user, require_scopes, current_user_id
import csv
from io import StringIO

import logging
logger = logging.getLogger(__name__)

router = APIRouter(tags=["Settings"], dependencies=[Depends(get_current_user)])
# ==============================
# CREATE - POST
# ==============================
@router.post("/", response_model=SettingRead)
async def create_setting_endpoint(
    setting_in: SettingCreate,
    db: AsyncSession = Depends(get_async_db),
    uid: str = Depends(current_user_id),
):
    try:
        new_setting, log = await create_setting(db, setting_in, uid)
        if log:
            db.add(log)
        await db.commit()
        # Opcional: log de éxito solo aquí (no es obligatorio, pero si quieres monitorear puedes dejarlo)
        logger.info(f"Marca creada exitosamente: {new_setting.id} - {new_setting.description} por usuario {uid}")
        return SettingRead.model_validate(new_setting)
    except IntegrityError as e:
        await db.rollback()
        logger.error("Error de integridad al crear marca: %s", e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error de integridad de datos: " + str(e.orig)
        )
    except SQLAlchemyError as e:
        await db.rollback()
        logger.error("Error de SQLAlchemy al crear marca: %s", e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error en la base de datos"
        )
    except Exception as e:
        await db.rollback()
        logger.exception("Error interno al crear marca", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno: {str(e)}"
        )

# ==============================
# GET ALL
# ==============================
@router.get("/", response_model=SettingListResponse)
async def list_settings(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = None,
    active: Optional[bool] = None,
    db: AsyncSession = Depends(get_async_db),
    uid: str = Depends(current_user_id),
):
    try:
        result = await get_settings(db, skip, limit, search, active, uid)
        await db.commit()
        return result
    except SQLAlchemyError as e:
        await db.rollback()
        logger.error("Error de base de datos al listar marcas: %s", e, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Ocurrió un error en la base de datos al obtener las marcas"
        )
    except Exception as e:
        await db.rollback()
        logger.exception("Error inesperado al listar marcas", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Ocurrió un error al obtener las marcas"
        )

# ==============================
# GET BY ID
# ==============================
@router.get("/{setting_id}", response_model=SettingRead)
async def read_setting(
    setting_id: UUID,
    db: AsyncSession = Depends(get_async_db),
    uid: str = Depends(current_user_id),
):
    try:
        setting = await get_setting_by_id(db, setting_id, uid)
        await db.commit()   # Registrar la auditoría si la hubo
        return SettingRead.model_validate(setting)
    except HTTPException as e:
        await db.rollback()
        logger.error("HTTPException al obtener la marca: %s", e.detail, exc_info=True)
        raise e
    except Exception as e:
        await db.rollback()
        logger.exception("Error inesperado al obtener la marca por ID", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Ocurrió un error al consultar la marca"
        )
        
# ==============================
# UPDATE - PUT
# ==============================
@router.put("/{setting_id}", response_model=SettingRead)
async def update_setting_endpoint(
    setting_id: UUID,
    setting_in: SettingUpdate,
    db: AsyncSession = Depends(get_async_db),
    uid: str = Depends(current_user_id),
):
    try:
        updated, log = await update_setting(db, setting_id, setting_in, uid)
        if not updated:
            raise HTTPException(status_code=404, detail="Marca no encontrada")
        if log:
            db.add(log)
        await db.commit()
        await db.refresh(updated)
        return SettingRead.model_validate(updated)
    except IntegrityError as e:
        await db.rollback()
        logger.error("Error de integridad al actualizar marca: %s", e, exc_info=True)
        raise HTTPException(
            status_code=400,
            detail="Error de integridad (nombre duplicado u otra restricción)."
        )
    except Exception as e:
        await db.rollback()
        logger.exception("Error inesperado al actualizar marca", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error interno: {str(e)}"
        )


# ==============================
# PARTIAL UPDATE - PATCH
# ==============================
@router.patch("/{setting_id}", response_model=SettingRead)
async def patch_setting_endpoint(
    setting_id: UUID,
    setting_in: SettingPatch,
    db: AsyncSession = Depends(get_async_db),
    uid: str = Depends(current_user_id),
):
    try:
        updated, log = await patch_setting(db, setting_id, setting_in, uid)
        if not updated:
            logger.warning(f"[patch_setting_endpoint] Marca {setting_id} no encontrada.")
            raise HTTPException(status_code=404, detail="Marca no encontrada")
        if log:
            db.add(log)
        await db.commit()
        await db.refresh(updated)
        logger.info(f"[patch_setting_endpoint] Marca {setting_id} actualizada parcialmente correctamente.")
        return SettingRead.model_validate(updated)
    except IntegrityError as e:
        await db.rollback()
        logger.error("Error de integridad al actualizar marca (PATCH): %s", e, exc_info=True)
        raise HTTPException(
            status_code=400,
            detail="Error de integridad (nombre duplicado u otra restricción)."
        )
    except HTTPException as e:
        await db.rollback()
        logger.error("HTTPException en patch_setting_endpoint: %s", e.detail, exc_info=True)
        raise e
    except Exception as e:
        await db.rollback()
        logger.exception("Error inesperado al actualizar marca (PATCH)", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error interno: {str(e)}"
        )

# ==============================
# IMPORT MASSIVE SETTINGS
# ==============================
@router.post("/import", status_code=201)
async def import_settings(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_async_db),
    uid: str = Depends(current_user_id),
):
    import csv
    from io import StringIO
    from sqlalchemy.exc import IntegrityError

    try:
        content = await file.read()
        csv_reader = csv.DictReader(StringIO(content.decode("utf-8")))
        if csv_reader.fieldnames:
            csv_reader.fieldnames = [h.strip().replace('\ufeff', '') for h in csv_reader.fieldnames]
            logger.info(f"Headers después de limpieza: {csv_reader.fieldnames}")
        settings = []
        count = 0
        user_id = uid
        for row in csv_reader:
            try:
                setting = Setting(
                    key=row["key"],
                    value=row.get("value", None),
                    type=row.get("type", "string"),
                    description=row.get("description", ""),
                    user_id=user_id,
                )
                settings.append(setting)
                count += 1
            except Exception as row_err:
                logger.warning(
                    "Fila con error en importación de configuración (fila %d): %s", count + 1, row_err, exc_info=True
                )
                # raise para abortar la importación en caso de error en fila, si lo prefieres

        if not settings:
            logger.warning("No se encontraron filas válidas para importar en el archivo CSV.")
            raise HTTPException(
                status_code=400,
                detail="No se encontraron filas válidas para importar."
            )

        db.add_all(settings)
        audit_level = await get_audit_level(db)    # Decidir si registrar el log según el nivel
        if audit_level > 1 and user_id:        
            await log_action(
                db,
                action="IMPORT",
                entity="Setting",
                description=f"Importación masiva: {len(settings)} configuraciones importadas.",
                user_id=user_id
            )
        await db.commit()
        logger.info("Importación masiva de configuraciones exitosa. Total importadas: %d", len(settings))
        return {"ok": True, "imported": len(settings)}

    except IntegrityError as e:
        await db.rollback()
        logger.error("Error de integridad en importación masiva: %s", e, exc_info=True)
        raise HTTPException(
            status_code=400,
            detail=f"Error de integridad (clave duplicada): {str(e.orig)}"
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