from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from uuid import UUID
from typing import List, Optional

from app.schemas.subgroup import (
    SubGroupCreate, SubGroupUpdate, SubGroupRead, SubGroupPatch, SubGroupImportResult, SubGroupListResponse
)
from app.crud.subgroup import (
    create_subgroup, get_subgroups, get_subgroup_by_id, update_subgroup, patch_subgroup
)
from app.models.user import User
from app.models.subgroup import SubGroup
from app.core.security import get_async_db
from app.utils.audit import log_action
import csv
from io import StringIO
from app.utils.audit_level import get_audit_level
from backend.app.dependencies.auth import get_current_user, require_scopes, current_user_id

import logging
logger = logging.getLogger(__name__)

router = APIRouter(tags=["SubGroups"], dependencies=[Depends(get_current_user)])
# ==============================
# CREATE - POST
# ==============================
@router.post("/", response_model=SubGroupRead)
async def create_subgroup_endpoint(
    subgroup_in: SubGroupCreate,
    db: AsyncSession = Depends(get_async_db),
    uid: str = Depends(current_user_id),
):
    try:
        new_subgroup, log = await create_subgroup(db, subgroup_in, uid)
        if log:
            db.add(log)
        await db.commit()
        # Opcional: log de éxito solo aquí (no es obligatorio, pero si quieres monitorear puedes dejarlo)
        logger.info(f"Subgrupo creado exitosamente: {new_subgroup.id} - {new_subgroup.name} por usuario {uid}")
        return SubGroupRead.model_validate(new_subgroup)
    except IntegrityError as e:
        await db.rollback()
        logger.error("Error de integridad al crear subgrupo: %s", e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error de integridad de datos: " + str(e.orig)
        )
    except SQLAlchemyError as e:
        await db.rollback()
        logger.error("Error de SQLAlchemy al crear subgrupo: %s", e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error en la base de datos"
        )
    except Exception as e:
        await db.rollback()
        logger.exception("Error interno al crear subgrupo", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno: {str(e)}"
        )

# ==============================
# GET ALL
# ==============================
@router.get("/", response_model=SubGroupListResponse)
async def list_subgroups(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = None,
    active: Optional[bool] = None,
    db: AsyncSession = Depends(get_async_db),
    uid: str = Depends(current_user_id),
):
    try:
        result = await get_subgroups(db, skip, limit, search, active, uid)
        await db.commit()
        return result
    except SQLAlchemyError as e:
        await db.rollback()
        logger.error("Error de base de datos al listar subgrupos: %s", e, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Ocurrió un error en la base de datos al obtener las subgrupos"
        )
    except Exception as e:
        await db.rollback()
        logger.exception("Error inesperado al listar subgrupos", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Ocurrió un error al obtener las subgrupos"
        )

# ==============================
# GET BY ID
# ==============================
@router.get("/{subgroup_id}", response_model=SubGroupRead)
async def read_subgroup(
    subgroup_id: UUID,
    db: AsyncSession = Depends(get_async_db),
    uid: str = Depends(current_user_id),
):
    try:
        subgroup = await get_subgroup_by_id(db, subgroup_id, uid)
        await db.commit()   # Registrar la auditoría si la hubo
        return SubGroupRead.model_validate(subgroup)
    except HTTPException as e:
        await db.rollback()
        logger.error("HTTPException al obtener la subgrupo: %s", e.detail, exc_info=True)
        raise e
    except Exception as e:
        await db.rollback()
        logger.exception("Error inesperado al obtener la subgrupo por ID", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Ocurrió un error al consultar la subgrupo"
        )
        
# ==============================
# UPDATE - PUT
# ==============================
@router.put("/{subgroup_id}", response_model=SubGroupRead)
async def update_subgroup_endpoint(
    subgroup_id: UUID,
    subgroup_in: SubGroupUpdate,
    db: AsyncSession = Depends(get_async_db),
    uid: str = Depends(current_user_id),
):
    try:
        updated, log = await update_subgroup(db, subgroup_id, subgroup_in, uid)
        if not updated:
            raise HTTPException(status_code=404, detail="Subgrupo no encontrado")
        if log:
            db.add(log)
        await db.commit()
        await db.refresh(updated)
        return SubGroupRead.model_validate(updated)
    except IntegrityError as e:
        await db.rollback()
        logger.error("Error de integridad al actualizar subgrupo: %s", e, exc_info=True)
        raise HTTPException(
            status_code=400,
            detail="Error de integridad (nombre duplicado u otra restricción)."
        )
    except Exception as e:
        await db.rollback()
        logger.exception("Error inesperado al actualizar subgrupo", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error interno: {str(e)}"
        )

# ==============================
# PARTIAL UPDATE - PATCH
# ==============================
@router.patch("/{subgroup_id}", response_model=SubGroupRead)
async def patch_subgroup_endpoint(
    subgroup_id: UUID,
    subgroup_in: SubGroupPatch,
    db: AsyncSession = Depends(get_async_db),
    uid: str = Depends(current_user_id),
):
    try:
        updated, log = await patch_subgroup(db, subgroup_id, subgroup_in, uid)
        if not updated:
            logger.warning(f"[patch_subgroup_endpoint] Subgrupo {subgroup_id} no encontrado.")
            raise HTTPException(status_code=404, detail="Subgrupo no encontrado")
        if log:
            db.add(log)
        await db.commit()
        await db.refresh(updated)
        logger.info(f"[patch_subgroup_endpoint] Subgrupo {subgroup_id} actualizado parcialmente.")
        return SubGroupRead.model_validate(updated)
    except IntegrityError as e:
        await db.rollback()
        logger.error("Error de integridad al actualizar subgrupo (PATCH): %s", e, exc_info=True)
        raise HTTPException(
            status_code=400,
            detail="Error de integridad (nombre duplicado u otra restricción)."
        )
    except HTTPException as e:
        await db.rollback()
        logger.error("HTTPException en patch_subgroup_endpoint: %s", e.detail, exc_info=True)
        raise e
    except Exception as e:
        await db.rollback()
        logger.exception("Error inesperado al actualizar subgrupo (PATCH)", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error interno: {str(e)}"
        )

# ==============================
# IMPORT MASSIVE BRANDS
# ==============================
@router.post("/import", status_code=201)
async def import_subgroups(
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
        subgroups = []
        user_id = uid
        count = 0
        for row in csv_reader:
            try:
                subgroup = SubGroup(
                    code=row["code"],
                    name=row["name"],
                    description=row.get("description", ""),
                    group_id= row["group_id"],
                    active=row.get("active", "true").lower() in ("true", "1", "yes", "si"),
                    user_id=uid
                )
                subgroups.append(subgroup)
                count += 1
            except Exception as row_err:
                logger.warning(
                    "Fila con error en importación de subgrupos (fila %d): %s", count + 1, row_err, exc_info=True
                )
                # Si prefieres abortar la importación ante fila errónea, lanza raise aquí

        if not subgroups:
            logger.warning("No se encontraron filas válidas para importar en el archivo CSV.")
            raise HTTPException(
                status_code=400,
                detail="No se encontraron filas válidas para importar."
            )
            
        db.add_all(subgroups)        
        audit_level = await get_audit_level(db)    # Decidir si registrar el log según el nivel
        if audit_level > 1 and user_id:        
            await log_action(
                db,
                action="IMPORT",
                entity="SubGroup",
                description=f"Importación masiva: {len(subgroups)} subgrupos importados.",
                user_id=user_id
            )
        await db.commit()
        logger.info("Importación masiva de subgrupos exitosa. Total importados: %d", len(subgroups))
        return {"ok": True, "imported": len(subgroups)}

    except IntegrityError as e:
        await db.rollback()
        logger.error("Error de integridad en importación masiva: %s", e, exc_info=True)
        raise HTTPException(
            status_code=400,
            detail=f"Error de integridad (subgrupo duplicado): {str(e.orig)}"
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