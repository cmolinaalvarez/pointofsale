from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from uuid import UUID
from typing import List, Optional

from app.schemas.group import (
    GroupCreate, GroupUpdate, GroupRead, GroupPatch, GroupImportResult, GroupListResponse
)
from app.crud.group import (
    create_group, get_groups, get_group_by_id, update_group, patch_group
)
from app.models.user import User
from app.models.group import Group
from app.core.security import get_async_db
from app.utils.audit import log_action
import csv
from io import StringIO
from app.utils.audit_level import get_audit_level
from app.dependencies.auth import get_current_user, require_scopes, current_user_id

import logging
logger = logging.getLogger(__name__)

router = APIRouter(tags=["Groups"], dependencies=[Depends(get_current_user)])
# ==============================
# CREATE - POST
# ==============================
@router.post("/", response_model=GroupRead)
async def create_group_endpoint(
    group_in: GroupCreate,
    db: AsyncSession = Depends(get_async_db),
    uid: str = Depends(current_user_id),
):
    try:
        new_group, log = await create_group(db, group_in, uid)
        if log:
            db.add(log)
        await db.commit()
        # Opcional: log de éxito solo aquí (no es obligatorio, pero si quieres monitorear puedes dejarlo)
        logger.info(f"Grupo creado exitosamente: {new_group.id} - {new_group.name} por usuario {uid}")
        return GroupRead.model_validate(new_group)
    except IntegrityError as e:
        await db.rollback()
        logger.error("Error de integridad al crear grupo: %s", e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error de integridad de datos: " + str(e.orig)
        )
    except SQLAlchemyError as e:
        await db.rollback()
        logger.error("Error de SQLAlchemy al crear grupo: %s", e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error en la base de datos"
        )
    except Exception as e:
        await db.rollback()
        logger.exception("Error interno al crear grupo", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno: {str(e)}"
        )

# ==============================
# GET ALL
# ==============================
@router.get("/", response_model=GroupListResponse)
async def list_groups(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = None,
    active: Optional[bool] = None,
    db: AsyncSession = Depends(get_async_db),
    uid: str = Depends(current_user_id),
):
    try:
        result = await get_groups(db, skip, limit, search, active, uid)
        await db.commit()
        return result
    except SQLAlchemyError as e:
        await db.rollback()
        logger.error("Error de base de datos al listar grupos: %s", e, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Ocurrió un error en la base de datos al obtener las grupos"
        )
    except Exception as e:
        await db.rollback()
        logger.exception("Error inesperado al listar grupos", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Ocurrió un error al obtener las grupos"
        )

# ==============================
# GET BY ID
# ==============================
@router.get("/{group_id}", response_model=GroupRead)
async def read_group(
    group_id: UUID,
    db: AsyncSession = Depends(get_async_db),
    uid: str = Depends(current_user_id),
):
    try:
        group = await get_group_by_id(db, group_id, uid)
        await db.commit()   # Registrar la auditoría si la hubo
        return GroupRead.model_validate(group)
    except HTTPException as e:
        await db.rollback()
        logger.error("HTTPException al obtener la grupo: %s", e.detail, exc_info=True)
        raise e
    except Exception as e:
        await db.rollback()
        logger.exception("Error inesperado al obtener la grupo por ID", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Ocurrió un error al consultar la grupo"
        )
        
# ==============================
# UPDATE - PUT
# ==============================
@router.put("/{group_id}", response_model=GroupRead)
async def update_group_endpoint(
    group_id: UUID,
    group_in: GroupUpdate,
    db: AsyncSession = Depends(get_async_db),
    uid: str = Depends(current_user_id),
):
    try:
        updated, log = await update_group(db, group_id, group_in, uid)
        if not updated:
            raise HTTPException(status_code=404, detail="Grupo no encontrado")
        if log:
            db.add(log)
        await db.commit()
        await db.refresh(updated)
        return GroupRead.model_validate(updated)
    except IntegrityError as e:
        await db.rollback()
        logger.error("Error de integridad al actualizar grupo: %s", e, exc_info=True)
        raise HTTPException(
            status_code=400,
            detail="Error de integridad (nombre duplicado u otra restricción)."
        )
    except Exception as e:
        await db.rollback()
        logger.exception("Error inesperado al actualizar grupo", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error interno: {str(e)}"
        )

# ==============================
# PARTIAL UPDATE - PATCH
# ==============================
@router.patch("/{group_id}", response_model=GroupRead)
async def patch_group_endpoint(
    group_id: UUID,
    group_in: GroupPatch,
    db: AsyncSession = Depends(get_async_db),
    uid: str = Depends(current_user_id),
):
    try:
        updated, log = await patch_group(db, group_id, group_in, uid)
        if not updated:
            logger.warning(f"[patch_group_endpoint] Grupo {group_id} no encontrado.")
            raise HTTPException(status_code=404, detail="Grupo no encontrado")
        if log:
            db.add(log)
        await db.commit()
        await db.refresh(updated)
        logger.info(f"[patch_group_endpoint] Grupo {group_id} actualizado parcialmente.")
        return GroupRead.model_validate(updated)
    except IntegrityError as e:
        await db.rollback()
        logger.error("Error de integridad al actualizar grupo (PATCH): %s", e, exc_info=True)
        raise HTTPException(
            status_code=400,
            detail="Error de integridad (nombre duplicado u otra restricción)."
        )
    except HTTPException as e:
        await db.rollback()
        logger.error("HTTPException en patch_group_endpoint: %s", e.detail, exc_info=True)
        raise e
    except Exception as e:
        await db.rollback()
        logger.exception("Error inesperado al actualizar grupo (PATCH)", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error interno: {str(e)}"
        )

# ==============================
# IMPORT MASSIVE BRANDS
# ==============================
@router.post("/import", status_code=201)
async def import_groups(
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
        groups = []
        user_id = uid
        count = 0
        for row in csv_reader:
            try:
                group = Group(
                    code=row["code"],
                    name=row["name"],
                    description=row.get("description", ""),
                    subcategory_id= row["subcategory_id"],
                    active=row.get("active", "true").lower() in ("true", "1", "yes", "si"),
                    user_id=uid
                )
                groups.append(group)
                count += 1
            except Exception as row_err:
                logger.warning(
                    "Fila con error en importación de grupos (fila %d): %s", count + 1, row_err, exc_info=True
                )
                # Si prefieres abortar la importación ante fila errónea, lanza raise aquí

        if not groups:
            logger.warning("No se encontraron filas válidas para importar en el archivo CSV.")
            raise HTTPException(
                status_code=400,
                detail="No se encontraron filas válidas para importar."
            )
            
        db.add_all(groups)        
        audit_level = await get_audit_level(db)    # Decidir si registrar el log según el nivel
        if audit_level > 1 and user_id:        
            await log_action(
                db,
                action="IMPORT",
                entity="Group",
                description=f"Importación masiva: {len(groups)} grupos importados.",
                user_id=user_id
            )
        await db.commit()
        logger.info("Importación masiva de grupos exitosa. Total importados: %d", len(groups))
        return {"ok": True, "imported": len(groups)}

    except IntegrityError as e:
        await db.rollback()
        logger.error("Error de integridad en importación masiva: %s", e, exc_info=True)
        raise HTTPException(
            status_code=400,
            detail=f"Error de integridad (grupo duplicado): {str(e.orig)}"
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