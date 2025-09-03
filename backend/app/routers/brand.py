from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from uuid import UUID
from typing import List, Optional

from app.schemas.brand import (
    BrandCreate, BrandUpdate, BrandRead, BrandPatch, BrandImportResult, BrandListResponse
)
from app.crud.brand import (
    create_brand, get_brands, get_brand_by_id, update_brand, patch_brand
)
from app.models.user import User
from app.models.brand import Brand
from app.core.security import get_async_db
from app.utils.audit import log_action
import csv
from io import StringIO
from app.utils.audit_level import get_audit_level
from app.dependencies.auth import get_current_user, require_scopes, current_user_id

import logging
logger = logging.getLogger(__name__)

router = APIRouter(tags=["Brands"], dependencies=[Depends(get_current_user)])
# ==============================
# CREATE - POST
# ==============================
@router.post("/", response_model=BrandRead)
async def create_brand_endpoint(
    brand_in: BrandCreate,
    db: AsyncSession = Depends(get_async_db),
    uid: str = Depends(current_user_id),
):
    try:
        new_brand, log = await create_brand(db, brand_in, uid)
        if log:
            db.add(log)
        await db.commit()
        # Opcional: log de éxito solo aquí (no es obligatorio, pero si quieres monitorear puedes dejarlo)
        logger.info(f"Marca creada exitosamente: {new_brand.id} - {new_brand.name} por usuario {uid}")
        return BrandRead.model_validate(new_brand)
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
@router.get("/", response_model=BrandListResponse)
async def list_brands(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = None,
    active: Optional[bool] = None,
    db: AsyncSession = Depends(get_async_db),
    uid: str = Depends(current_user_id),
):
    try:
        result = await get_brands(db, skip, limit, search, active, uid)
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
@router.get("/{brand_id}", response_model=BrandRead)
async def read_brand(
    brand_id: UUID,
    db: AsyncSession = Depends(get_async_db),
    uid: str = Depends(current_user_id),
):
    try:
        brand = await get_brand_by_id(db, brand_id, uid)
        await db.commit()   # Registrar la auditoría si la hubo
        return BrandRead.model_validate(brand)
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
@router.put("/{brand_id}", response_model=BrandRead)
async def update_brand_endpoint(
    brand_id: UUID,
    brand_in: BrandUpdate,
    db: AsyncSession = Depends(get_async_db),
    uid: str = Depends(current_user_id),
):
    try:
        updated, log = await update_brand(db, brand_id, brand_in, uid)
        if not updated:
            raise HTTPException(status_code=404, detail="Marca no encontrada")
        if log:
            db.add(log)
        await db.commit()
        await db.refresh(updated)
        return BrandRead.model_validate(updated)
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
@router.patch("/{brand_id}", response_model=BrandRead)
async def patch_brand_endpoint(
    brand_id: UUID,
    brand_in: BrandPatch,
    db: AsyncSession = Depends(get_async_db),
    uid: str = Depends(current_user_id),
):
    try:
        updated, log = await patch_brand(db, brand_id, brand_in, uid)
        if not updated:
            logger.warning(f"[patch_brand_endpoint] Marca {brand_id} no encontrada.")
            raise HTTPException(status_code=404, detail="Marca no encontrada")
        if log:
            db.add(log)
        await db.commit()
        await db.refresh(updated)
        logger.info(f"[patch_brand_endpoint] Marca {brand_id} actualizada parcialmente correctamente.")
        return BrandRead.model_validate(updated)
    except IntegrityError as e:
        await db.rollback()
        logger.error("Error de integridad al actualizar marca (PATCH): %s", e, exc_info=True)
        raise HTTPException(
            status_code=400,
            detail="Error de integridad (nombre duplicado u otra restricción)."
        )
    except HTTPException as e:
        await db.rollback()
        logger.error("HTTPException en patch_brand_endpoint: %s", e.detail, exc_info=True)
        raise e
    except Exception as e:
        await db.rollback()
        logger.exception("Error inesperado al actualizar marca (PATCH)", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error interno: {str(e)}"
        )

# ==============================
# IMPORT MASSIVE BRANDS
# ==============================
@router.post("/import", status_code=201)
async def import_brands(
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
        brands = []
        user_id = uid
        count = 0
        for row in csv_reader:
            try:
                brand = Brand(
                    code=row["code"],
                    name=row["name"],
                    description=row.get("description", ""),
                    active=row.get("active", "true").lower() in ("true", "1", "yes", "si"),
                    user_id=uid
                )
                brands.append(brand)
                count += 1
            except Exception as row_err:
                logger.warning(
                    "Fila con error en importación de marcas (fila %d): %s", count + 1, row_err, exc_info=True
                )
                # Si prefieres abortar la importación ante fila errónea, lanza raise aquí

        if not brands:
            logger.warning("No se encontraron filas válidas para importar en el archivo CSV.")
            raise HTTPException(
                status_code=400,
                detail="No se encontraron filas válidas para importar."
            )
            
        db.add_all(brands)        
        audit_level = await get_audit_level(db)    # Decidir si registrar el log según el nivel
        if audit_level > 1 and user_id:        
            await log_action(
                db,
                action="IMPORT",
                entity="Brand",
                description=f"Importación masiva: {len(brands)} marcas importadas.",
                user_id=user_id
            )
        await db.commit()
        logger.info("Importación masiva de marcas exitosa. Total importadas: %d", len(brands))
        return {"ok": True, "imported": len(brands)}

    except IntegrityError as e:
        await db.rollback()
        logger.error("Error de integridad en importación masiva: %s", e, exc_info=True)
        raise HTTPException(
            status_code=400,
            detail=f"Error de integridad (marca duplicada): {str(e.orig)}"
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