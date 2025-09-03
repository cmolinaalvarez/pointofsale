from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from uuid import UUID
from typing import List, Optional

from app.schemas.subcategory import (
    SubCategoryCreate, SubCategoryUpdate, SubCategoryRead, SubCategoryPatch, SubCategoryImportResult, SubCategoryListResponse
)
from app.crud.subcategory import (
    create_subcategory, get_subcategories, get_subcategory_by_id, update_subcategory, patch_subcategory
)
from app.models.user import User
from app.models.subcategory import SubCategory
from app.core.security import get_async_db
from app.utils.audit import log_action
import csv
from io import StringIO
from app.utils.audit_level import get_audit_level
from app.dependencies.auth import get_current_user, require_scopes, current_user_id

import logging
logger = logging.getLogger(__name__)

router = APIRouter(tags=["SubCategories"], dependencies=[Depends(get_current_user)])
# ==============================
# CREATE - POST
# ==============================
@router.post("/", response_model=SubCategoryRead)
async def create_subcategory_endpoint(
    subcategory_in: SubCategoryCreate,
    db: AsyncSession = Depends(get_async_db),
    uid: str = Depends(current_user_id),
):
    try:
        new_subcategory, log = await create_subcategory(db, subcategory_in, uid)
        if log:
            db.add(log)
        await db.commit()
        # Opcional: log de éxito solo aquí (no es obligatorio, pero si quieres monitorear puedes dejarlo)
        logger.info(f"Subcategoría creada exitosamente: {new_subcategory.id} - {new_subcategory.name} por usuario {uid}")
        return SubCategoryRead.model_validate(new_subcategory)
    except IntegrityError as e:
        await db.rollback()
        logger.error("Error de integridad al crear subcategoría: %s", e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error de integridad de datos: " + str(e.orig)
        )
    except SQLAlchemyError as e:
        await db.rollback()
        logger.error("Error de SQLAlchemy al crear subcategoría: %s", e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error en la base de datos"
        )
    except Exception as e:
        await db.rollback()
        logger.exception("Error interno al crear subcategoría", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno: {str(e)}"
        )

# ==============================
# GET ALL
# ==============================
@router.get("/", response_model=SubCategoryListResponse)
async def list_subcategories(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = None,
    active: Optional[bool] = None,
    db: AsyncSession = Depends(get_async_db),
    uid: str = Depends(current_user_id),
):
    try:
        result = await get_subcategories(db, skip, limit, search, active, uid)
        await db.commit()
        return result
    except SQLAlchemyError as e:
        await db.rollback()
        logger.error("Error de base de datos al listar subcategorías: %s", e, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Ocurrió un error en la base de datos al obtener las subcategorías"
        )
    except Exception as e:
        await db.rollback()
        logger.exception("Error inesperado al listar subcategorías", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Ocurrió un error al obtener las subcategorías"
        )

# ==============================
# GET BY ID
# ==============================
@router.get("/{subcategory_id}", response_model=SubCategoryRead)
async def read_subcategory(
    subcategory_id: UUID,
    db: AsyncSession = Depends(get_async_db),
    uid: str = Depends(current_user_id),
):
    try:
        subcategory = await get_subcategory_by_id(db, subcategory_id, uid)
        await db.commit()   # Registrar la auditoría si la hubo
        return SubCategoryRead.model_validate(subcategory)
    except HTTPException as e:
        await db.rollback()
        logger.error("HTTPException al obtener la subcategoría: %s", e.detail, exc_info=True)
        raise e
    except Exception as e:
        await db.rollback()
        logger.exception("Error inesperado al obtener la subcategoría por ID", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Ocurrió un error al consultar la subcategoría"
        )
        
# ==============================
# UPDATE - PUT
# ==============================
@router.put("/{subcategory_id}", response_model=SubCategoryRead)
async def update_subcategory_endpoint(
    subcategory_id: UUID,
    subcategory_in: SubCategoryUpdate,
    db: AsyncSession = Depends(get_async_db),
    uid: str = Depends(current_user_id),
):
    try:
        updated, log = await update_subcategory(db, subcategory_id, subcategory_in, uid)
        if not updated:
            raise HTTPException(status_code=404, detail="Marca no encontrada")
        if log:
            db.add(log)
        await db.commit()
        await db.refresh(updated)
        return SubCategoryRead.model_validate(updated)
    except IntegrityError as e:
        await db.rollback()
        logger.error("Error de integridad al actualizar subcategoría: %s", e, exc_info=True)
        raise HTTPException(
            status_code=400,
            detail="Error de integridad (nombre duplicado u otra restricción)."
        )
    except Exception as e:
        await db.rollback()
        logger.exception("Error inesperado al actualizar subcategoría", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error interno: {str(e)}"
        )

# ==============================
# PARTIAL UPDATE - PATCH
# ==============================
@router.patch("/{subcategory_id}", response_model=SubCategoryRead)
async def patch_subcategory_endpoint(
    subcategory_id: UUID,
    subcategory_in: SubCategoryPatch,
    db: AsyncSession = Depends(get_async_db),
    uid: str = Depends(current_user_id),
):
    try:
        updated, log = await patch_subcategory(db, subcategory_id, subcategory_in, uid)
        if not updated:
            logger.warning(f"[patch_subcategory_endpoint] Marca {subcategory_id} no encontrada.")
            raise HTTPException(status_code=404, detail="Marca no encontrada")
        if log:
            db.add(log)
        await db.commit()
        await db.refresh(updated)
        logger.info(f"[patch_subcategory_endpoint] Marca {subcategory_id} actualizada parcialmente correctamente.")
        return SubCategoryRead.model_validate(updated)
    except IntegrityError as e:
        await db.rollback()
        logger.error("Error de integridad al actualizar subcategoría (PATCH): %s", e, exc_info=True)
        raise HTTPException(
            status_code=400,
            detail="Error de integridad (nombre duplicado u otra restricción)."
        )
    except HTTPException as e:
        await db.rollback()
        logger.error("HTTPException en patch_subcategory_endpoint: %s", e.detail, exc_info=True)
        raise e
    except Exception as e:
        await db.rollback()
        logger.exception("Error inesperado al actualizar subcategoría (PATCH)", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error interno: {str(e)}"
        )

# ==============================
# IMPORT MASSIVE BRANDS
# ==============================
@router.post("/import", status_code=201)
async def import_subcategorys(
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
        subcategorys = []
        user_id = uid
        count = 0
        for row in csv_reader:
            try:
                subcategory = SubCategory(
                    code=row["code"],
                    name=row["name"],
                    description=row.get("description", ""),
                    category_id= row["category_id"],
                    active=row.get("active", "true").lower() in ("true", "1", "yes", "si"),
                    user_id=uid
                )
                subcategorys.append(subcategory)
                count += 1
            except Exception as row_err:
                logger.warning(
                    "Fila con error en importación de subcategorías (fila %d): %s", count + 1, row_err, exc_info=True
                )
                # Si prefieres abortar la importación ante fila errónea, lanza raise aquí

        if not subcategorys:
            logger.warning("No se encontraron filas válidas para importar en el archivo CSV.")
            raise HTTPException(
                status_code=400,
                detail="No se encontraron filas válidas para importar."
            )
            
        db.add_all(subcategorys)        
        audit_level = await get_audit_level(db)    # Decidir si registrar el log según el nivel
        if audit_level > 1 and user_id:        
            await log_action(
                db,
                action="IMPORT",
                entity="SubCategory",
                description=f"Importación masiva: {len(subcategorys)} subcategorías importadas.",
                user_id=user_id
            )
        await db.commit()
        logger.info("Importación masiva de subcategorías exitosa. Total importadas: %d", len(subcategorys))
        return {"ok": True, "imported": len(subcategorys)}

    except IntegrityError as e:
        await db.rollback()
        logger.error("Error de integridad en importación masiva: %s", e, exc_info=True)
        raise HTTPException(
            status_code=400,
            detail=f"Error de integridad (subcategoría duplicada): {str(e.orig)}"
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