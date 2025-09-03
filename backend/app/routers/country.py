from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from uuid import UUID
from typing import List, Optional

from app.schemas.country import (
    CountryCreate, CountryUpdate, CountryRead, CountryPatch, CountryImportResult, CountryListResponse
)
from app.crud.country import (
    create_country, get_countrys, get_country_by_id, update_country, patch_country
)
from app.models.user import User
from app.models.country import Country
from app.core.security import get_async_db
from app.utils.audit import log_action
import csv
from io import StringIO
from app.utils.audit_level import get_audit_level
from backend.app.dependencies.auth import get_current_user, require_scopes, current_user_id

import logging
logger = logging.getLogger(__name__)

router = APIRouter(tags=["Countries"], dependencies=[Depends(get_current_user)])
# ==============================
# CREATE - POST
# ==============================
@router.post("/", response_model=CountryRead)
async def create_country_endpoint(
    country_in: CountryCreate,
    db: AsyncSession = Depends(get_async_db),
    uid: str = Depends(current_user_id),
):
    try:
        new_country, log = await create_country(db, country_in, uid)
        if log:
            db.add(log)
        await db.commit()
        # Opcional: log de éxito solo aquí (no es obligatorio, pero si quieres monitorear puedes dejarlo)
        logger.info(f"País creado exitosamente: {new_country.id} - {new_country.name} por usuario {uid}")
        return CountryRead.model_validate(new_country)
    except IntegrityError as e:
        await db.rollback()
        logger.error("Error de integridad al crear país: %s", e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error de integridad de datos: " + str(e.orig)
        )
    except SQLAlchemyError as e:
        await db.rollback()
        logger.error("Error de SQLAlchemy al crear país: %s", e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error en la base de datos"
        )
    except Exception as e:
        await db.rollback()
        logger.exception("Error interno al crear el país", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno: {str(e)}"
        )

# ==============================
# GET ALL
# ==============================
@router.get("/", response_model=CountryListResponse)
async def list_countries(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = None,
    active: Optional[bool] = None,
    db: AsyncSession = Depends(get_async_db),
    uid: str = Depends(current_user_id),
):
    try:
        result = await get_countrys(db, skip, limit, search, active, uid)
        await db.commit()
        return result
    except SQLAlchemyError as e:
        await db.rollback()
        logger.error("Error de base de datos al listar paises: %s", e, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Ocurrió un error en la base de datos al obtener las paises"
        )
    except Exception as e:
        await db.rollback()
        logger.exception("Error inesperado al listar paises", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Ocurrió un error al obtener las paises"
        )

# ==============================
# GET BY ID
# ==============================
@router.get("/{country_id}", response_model=CountryRead)
async def read_country(
    country_id: UUID,
    db: AsyncSession = Depends(get_async_db),
    uid: str = Depends(current_user_id),
):
    try:
        country = await get_country_by_id(db, country_id, uid)
        await db.commit()   # Registrar la auditoría si la hubo
        return CountryRead.model_validate(country)
    except HTTPException as e:
        await db.rollback()
        logger.error("HTTPException al obtener la país: %s", e.detail, exc_info=True)
        raise e
    except Exception as e:
        await db.rollback()
        logger.exception("Error inesperado al obtener la país por ID", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Ocurrió un error al consultar la país"
        )
        
# ==============================
# UPDATE - PUT
# ==============================
@router.put("/{country_id}", response_model=CountryRead)
async def update_country_endpoint(
    country_id: UUID,
    country_in: CountryUpdate,
    db: AsyncSession = Depends(get_async_db),
    uid: str = Depends(current_user_id),
):
    try:
        updated, log = await update_country(db, country_id, country_in, uid)
        if not updated:
            raise HTTPException(status_code=404, detail="País no encontrado")
        if log:
            db.add(log)
        await db.commit()
        await db.refresh(updated)
        return CountryRead.model_validate(updated)
    except IntegrityError as e:
        await db.rollback()
        logger.error("Error de integridad al actualizar el país: %s", e, exc_info=True)
        raise HTTPException(
            status_code=400,
            detail="Error de integridad (nombre duplicado u otra restricción)."
        )
    except Exception as e:
        await db.rollback()
        logger.exception("Error inesperado al actualizar el país", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error interno: {str(e)}"
        )

# ==============================
# PARTIAL UPDATE - PATCH
# ==============================
@router.patch("/{country_id}", response_model=CountryRead)
async def patch_country_endpoint(
    country_id: UUID,
    country_in: CountryPatch,
    db: AsyncSession = Depends(get_async_db),
    uid: str = Depends(current_user_id),
):
    try:
        updated, log = await patch_country(db, country_id, country_in, uid)
        if not updated:
            logger.warning(f"[patch_country_endpoint] País {country_id} no encontrado.")
            raise HTTPException(status_code=404, detail="País no encontrada")
        if log:
            db.add(log)
        await db.commit()
        await db.refresh(updated)
        logger.info(f"[patch_country_endpoint] País {country_id} actualizado parcialmente correctamente.")
        return CountryRead.model_validate(updated)
    except IntegrityError as e:
        await db.rollback()
        logger.error("Error de integridad al actualizar el país (PATCH): %s", e, exc_info=True)
        raise HTTPException(
            status_code=400,
            detail="Error de integridad (nombre duplicado u otra restricción)."
        )
    except HTTPException as e:
        await db.rollback()
        logger.error("HTTPException en patch_country_endpoint: %s", e.detail, exc_info=True)
        raise e
    except Exception as e:
        await db.rollback()
        logger.exception("Error inesperado al actualizar el país (PATCH)", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error interno: {str(e)}"
        )

# ==============================
# IMPORT MASSIVE BRANDS
# ==============================
@router.post("/import", status_code=201)
async def import_countries(
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
        countrys = []
        user_id = uid
        count = 0
        for row in csv_reader:
            try:
                country = Country(
                    code=row["code"],
                    name=row["name"], 
                    country_code=row["country_code"],                   
                    active=row.get("active", "true").lower() in ("true", "1", "yes", "si"),
                    user_id=uid
                )
                countrys.append(country)
                count += 1
            except Exception as row_err:
                logger.warning(
                    "Fila con error en importación de paises (fila %d): %s", count + 1, row_err, exc_info=True
                )
                # Si prefieres abortar la importación ante fila errónea, lanza raise aquí

        if not countrys:
            logger.warning("No se encontraron filas válidas para importar en el archivo CSV.")
            raise HTTPException(
                status_code=400,
                detail="No se encontraron filas válidas para importar."
            )
            
        db.add_all(countrys)        
        audit_level = await get_audit_level(db)    # Decidir si registrar el log según el nivel
        if audit_level > 1 and user_id:        
            await log_action(
                db,
                action="IMPORT",
                entity="Country",
                description=f"Importación masiva: {len(countrys)} paises importados.",
                user_id=user_id
            )
        await db.commit()
        logger.info("Importación masiva de paises exitosa. Total importadas: %d", len(countrys))
        return {"ok": True, "imported": len(countrys)}

    except IntegrityError as e:
        await db.rollback()
        logger.error("Error de integridad en importación masiva: %s", e, exc_info=True)
        raise HTTPException(
            status_code=400,
            detail=f"Error de integridad (país duplicado): {str(e.orig)}"
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