from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from uuid import UUID
from typing import List, Optional

from app.schemas.category import (
    CategoryCreate, CategoryUpdate, CategoryRead, CategoryPatch, CategoryImportResult, CategoryListResponse
)
from app.crud.category import (
    create_category, get_categories, get_category_by_id, update_category, patch_category
)
from app.models.user import User
from app.models.category import Category
from app.core.security import get_async_db
from app.utils.audit import log_action
import csv
from io import StringIO
from app.utils.audit_level import get_audit_level
from backend.app.dependencies.auth import get_current_user, require_scopes, current_user_id

import logging
logger = logging.getLogger(__name__)

router = APIRouter(tags=["Categories"], dependencies=[Depends(get_current_user)])
# ==============================
# CREATE - POST
# ==============================
@router.post("/", response_model=CategoryRead)
async def create_category_endpoint(
    category_in: CategoryCreate,
    db: AsyncSession = Depends(get_async_db),
    uid: str = Depends(current_user_id),
):
    try:
        new_category, log = await create_category(db, category_in, uid)
        if log:
            db.add(log)
        await db.commit()
        # Opcional: log de éxito solo aquí (no es obligatorio, pero si quieres monitorear puedes dejarlo)
        logger.info(f"Categoría creada exitosamente: {new_category.id} - {new_category.name} por usuario {uid}")
        return CategoryRead.model_validate(new_category)
    except IntegrityError as e:
        await db.rollback()
        logger.error("Error de integridad al crear la categoría: %s", e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error de integridad de datos: " + str(e.orig)
        )
    except SQLAlchemyError as e:
        await db.rollback()
        logger.error("Error de SQLAlchemy al crear categoría: %s", e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error en la base de datos"
        )
    except Exception as e:
        await db.rollback()
        logger.exception("Error interno al crear categoría", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno: {str(e)}"
        )

# ==============================
# GET ALL
# ==============================
@router.get("/", response_model=CategoryListResponse)
async def list_categories(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = None,
    active: Optional[bool] = None,
    db: AsyncSession = Depends(get_async_db),
    uid: str = Depends(current_user_id),
):
    try:
        result = await get_categories(db, skip, limit, search, active, uid)
        await db.commit()
        return result
    except SQLAlchemyError as e:
        await db.rollback()
        logger.error("Error de base de datos al listar categorias: %s", e, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Ocurrió un error en la base de datos al obtener las categorias"
        )
    except Exception as e:
        await db.rollback()
        logger.exception("Error inesperado al listar categorias", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Ocurrió un error al obtener las categorias"
        )

# ==============================
# GET BY ID
# ==============================
@router.get("/{category_id}", response_model=CategoryRead)
async def read_category(
    category_id: UUID,
    db: AsyncSession = Depends(get_async_db),
    uid: str = Depends(current_user_id),
):
    try:
        category = await get_category_by_id(db, category_id, uid)
        await db.commit()   # Registrar la auditoría si la hubo
        return CategoryRead.model_validate(category)
    except HTTPException as e:
        await db.rollback()
        logger.error("HTTPException al obtener la categoría: %s", e.detail, exc_info=True)
        raise e
    except Exception as e:
        await db.rollback()
        logger.exception("Error inesperado al obtener la categoría por ID", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Ocurrió un error al consultar la categoría"
        )
        
# ==============================
# UPDATE - PUT
# ==============================
@router.put("/{category_id}", response_model=CategoryRead)
async def update_category_endpoint(
    category_id: UUID,
    category_in: CategoryUpdate,
    db: AsyncSession = Depends(get_async_db),
    uid: str = Depends(current_user_id),
):
    try:
        updated, log = await update_category(db, category_id, category_in, uid)
        if not updated:
            raise HTTPException(status_code=404, detail="Categoría no encontrada")
        if log:
            db.add(log)
        await db.commit()
        await db.refresh(updated)
        return CategoryRead.model_validate(updated)
    except IntegrityError as e:
        await db.rollback()
        logger.error("Error de integridad al actualizar categoría: %s", e, exc_info=True)
        raise HTTPException(
            status_code=400,
            detail="Error de integridad (nombre duplicado u otra restricción)."
        )
    except Exception as e:
        await db.rollback()
        logger.exception("Error inesperado al actualizar categoría", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error interno: {str(e)}"
        )

# ==============================
# PARTIAL UPDATE - PATCH
# ==============================
@router.patch("/{category_id}", response_model=CategoryRead)
async def patch_category_endpoint(
    category_id: UUID,
    category_in: CategoryPatch,
    db: AsyncSession = Depends(get_async_db),
    uid: str = Depends(current_user_id),
):
    try:
        updated, log = await patch_category(db, category_id, category_in, uid)
        if not updated:
            logger.warning(f"[patch_category_endpoint] Categoría {category_id} no encontrada.")
            raise HTTPException(status_code=404, detail="Categoría no encontrada")
        if log:
            db.add(log)
        await db.commit()
        await db.refresh(updated)
        logger.info(f"[patch_category_endpoint] Categoría {category_id} actualizada parcialmente correctamente.")
        return CategoryRead.model_validate(updated)
    except IntegrityError as e:
        await db.rollback()
        logger.error("Error de integridad al actualizar la categoría (PATCH): %s", e, exc_info=True)
        raise HTTPException(
            status_code=400,
            detail="Error de integridad (nombre duplicado u otra restricción)."
        )
    except HTTPException as e:
        await db.rollback()
        logger.error("HTTPException en patch_category_endpoint: %s", e.detail, exc_info=True)
        raise e
    except Exception as e:
        await db.rollback()
        logger.exception("Error inesperado al actualizar categoría (PATCH)", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error interno: {str(e)}"
        )

# ==============================
# IMPORT MASSIVE BRANDS
# ==============================
@router.post("/import", status_code=201)
async def import_categories(
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
        categories = []
        user_id = uid
        count = 0
        for row in csv_reader:
            try:
                category = Category(
                    code=row["code"],
                    name=row["name"],
                    description=row.get("description", ""),
                    active=row.get("active", "true").lower() in ("true", "1", "yes", "si"),
                    user_id=uid
                )
                categories.append(category)
                count += 1
            except Exception as row_err:
                logger.warning(
                    "Fila con error en importación de categorias (fila %d): %s", count + 1, row_err, exc_info=True
                )
                # Si prefieres abortar la importación ante fila errónea, lanza raise aquí

        if not categories:
            logger.warning("No se encontraron filas válidas para importar en el archivo CSV.")
            raise HTTPException(
                status_code=400,
                detail="No se encontraron filas válidas para importar."
            )
            
        db.add_all(categories)        
        audit_level = await get_audit_level(db)    # Decidir si registrar el log según el nivel
        if audit_level > 1 and user_id:        
            await log_action(
                db,
                action="IMPORT",
                entity="Category",
                description=f"Importación masiva: {len(categories)} categorias importadas.",
                user_id=user_id
            )
        await db.commit()
        logger.info("Importación masiva de categorias exitosa. Total importadas: %d", len(categories))
        return {"ok": True, "imported": len(categories)}

    except IntegrityError as e:
        await db.rollback()
        logger.error("Error de integridad en importación masiva: %s", e, exc_info=True)
        raise HTTPException(
            status_code=400,
            detail=f"Error de integridad (categoría duplicada): {str(e.orig)}"
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