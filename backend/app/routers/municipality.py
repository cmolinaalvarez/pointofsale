from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from uuid import UUID
from typing import List, Optional

from app.schemas.municipality import (
    MunicipalityCreate, MunicipalityUpdate, MunicipalityRead, MunicipalityPatch, MunicipalityImportResult, MunicipalityListResponse
)
from app.crud.municipality import (
    create_municipality, get_municipalities, get_municipality_by_id, update_municipality, patch_municipality
)
from app.models.user import User
from app.models.municipality import Municipality
from app.models.division import Division
from app.core.security import get_async_db
from app.utils.audit import log_action
import csv
from io import StringIO
from app.utils.audit_level import get_audit_level
from backend.app.dependencies.auth import get_current_user, require_scopes, current_user_id

import logging
logger = logging.getLogger(__name__)

router = APIRouter(tags=["Municipalities"], dependencies=[Depends(get_current_user)])
# ==============================
# CREATE - POST
# ==============================
@router.post("/", response_model=MunicipalityRead)
async def create_municipality_endpoint(
    municipality_in: MunicipalityCreate,
    db: AsyncSession = Depends(get_async_db),
    uid: str = Depends(current_user_id),
):
    try:
        new_municipality, log = await create_municipality(db, municipality_in, uid)
        if log:
            db.add(log)
        await db.commit()
        # Opcional: log de éxito solo aquí (no es obligatorio, pero si quieres monitorear puedes dejarlo)
        logger.info(f"municipio creada exitosamente: {new_municipality.id} - {new_municipality.name} por usuario {uid}")
        return MunicipalityRead.model_validate(new_municipality)
    except IntegrityError as e:
        await db.rollback()
        logger.error("Error de integridad al crear el municipio: %s", e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error de integridad de datos: " + str(e.orig)
        )
    except SQLAlchemyError as e:
        await db.rollback()
        logger.error("Error de SQLAlchemy al crear el municipio: %s", e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error en la base de datos"
        )
    except Exception as e:
        await db.rollback()
        logger.exception("Error interno al crear el municipio", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno: {str(e)}"
        )

# ==============================
# GET ALL
# ==============================
@router.get("/", response_model=MunicipalityListResponse)
async def list_municipalities(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = None,
    active: Optional[bool] = None,
    db: AsyncSession = Depends(get_async_db),
    uid: str = Depends(current_user_id),
):
    try:
        result = await get_municipalities(db, skip, limit, search, active, uid)
        await db.commit()
        return result
    except SQLAlchemyError as e:
        await db.rollback()
        logger.error("Error de base de datos al listar los municipios: %s", e, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Ocurrió un error en la base de datos al obtener las municipios"
        )
    except Exception as e:
        await db.rollback()
        logger.exception("Error inesperado al listar los municipios", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Ocurrió un error al obtener los municipios"
        )

# ==============================
# GET BY ID
# ==============================
@router.get("/{municipality_id}", response_model=MunicipalityRead)
async def read_municipality(
    municipality_id: UUID,
    db: AsyncSession = Depends(get_async_db),
    uid: str = Depends(current_user_id),
):
    try:
        municipality = await get_municipality_by_id(db, municipality_id, uid)
        await db.commit()   # Registrar la auditoría si la hubo
        return MunicipalityRead.model_validate(municipality)
    except HTTPException as e:
        await db.rollback()
        logger.error("HTTPException al obtener el municipio: %s", e.detail, exc_info=True)
        raise e
    except Exception as e:
        await db.rollback()
        logger.exception("Error inesperado al obtener el municipio por ID", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Ocurrió un error al consultar el municipio"
        )
        
# ==============================
# UPDATE - PUT
# ==============================
@router.put("/{municipality_id}", response_model=MunicipalityRead)
async def update_municipality_endpoint(
    municipality_id: UUID,
    municipality_in: MunicipalityUpdate,
    db: AsyncSession = Depends(get_async_db),
    uid: str = Depends(current_user_id),
):
    try:
        updated, log = await update_municipality(db, municipality_id, municipality_in, uid)
        if not updated:
            raise HTTPException(status_code=404, detail="Municipio no encontrado")
        if log:
            db.add(log)
        await db.commit()
        # updated ahora es un diccionario, no necesita refresh
        return MunicipalityRead.model_validate(updated)
    except IntegrityError as e:
        await db.rollback()
        logger.error("Error de integridad al actualizar el municipio: %s", e, exc_info=True)
        raise HTTPException(
            status_code=400,
            detail="Error de integridad (nombre duplicado u otra restricción)."
        )
    except Exception as e:
        await db.rollback()
        logger.exception("Error inesperado al actualizar el municipio", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error interno: {str(e)}"
        )

# ==============================
# PARTIAL UPDATE - PATCH
# ==============================
@router.patch("/{municipality_id}", response_model=MunicipalityRead)
async def patch_municipality_endpoint(
    municipality_id: UUID,
    municipality_in: MunicipalityPatch,
    db: AsyncSession = Depends(get_async_db),
    uid: str = Depends(current_user_id),
):
    try:
        updated, log = await patch_municipality(db, municipality_id, municipality_in, uid)
        if not updated:
            logger.warning(f"[patch_municipality_endpoint] municipio {municipality_id} no encontrado.")
            raise HTTPException(status_code=404, detail="municipio no encontrado")
        if log:
            db.add(log)
        await db.commit()
        await db.refresh(updated)
        logger.info(f"[patch_municipality_endpoint] municipio {municipality_id} actualizada parcialmente correctamente.")
        return MunicipalityRead.model_validate(updated)
    except IntegrityError as e:
        await db.rollback()
        logger.error("Error de integridad al actualizar el municipio (PATCH): %s", e, exc_info=True)
        raise HTTPException(
            status_code=400,
            detail="Error de integridad (nombre duplicado u otra restricción)."
        )
    except HTTPException as e:
        await db.rollback()
        logger.error("HTTPException en patch_municipality_endpoint: %s", e.detail, exc_info=True)
        raise e
    except Exception as e:
        await db.rollback()
        logger.exception("Error inesperado al actualizar el municipio (PATCH)", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error interno: {str(e)}"
        )

# ==============================
# IMPORT MASSIVE BRANDS
# ==============================
@router.post("/import", status_code=201)
async def import_municipalities(
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
        municipalitys = []
        user_id = uid
        count = 0
        for row in csv_reader:
            result = await db.execute(select(Division).where(Division.code == row["division_code"]))
            division = result.scalars().first()  
            if division:
                try:
                    municipality = Municipality(
                        code=row["code"],
                        name=row["name"],
                        division_id=division.id,
                        active=row.get("active", "true").lower() in ("true", "1", "yes", "si"),
                        user_id=uid
                    )
                    municipalitys.append(municipality)
                    count += 1
                except Exception as row_err:
                    logger.warning(
                        "Fila con error en importación de municipios (fila %d): %s", count + 1, row_err, exc_info=True
                    )
                    # Si prefieres abortar la importación ante fila errónea, lanza raise aquí
            else:
                logger.warning(
                        "Fila con error en importación de municipalities (fila %d): %s", count + 1,  exc_info=True
                ) 
                raise HTTPException(
                status_code=400,
                detail = "La fila " + str(count + 1) + " no tiene un division_code."
            )              

        if not municipalitys:
            logger.warning("No se encontraron filas válidas para importar en el archivo CSV.")
            raise HTTPException(
                status_code=400,
                detail="No se encontraron filas válidas para importar."
            )
            
        db.add_all(municipalitys)        
        audit_level = await get_audit_level(db)    # Decidir si registrar el log según el nivel
        if audit_level > 1 and user_id:        
            await log_action(
                db,
                action="IMPORT",
                entity="Municipality",
                description=f"Importación masiva: {len(municipalitys)} municipios importadas.",
                user_id=user_id
            )
        await db.commit()
        logger.info("Importación masiva del municipio exitosa. Total importadas: %d", len(municipalitys))
        return {"ok": True, "imported": len(municipalitys)}

    except IntegrityError as e:
        await db.rollback()
        logger.error("Error de integridad en importación masiva: %s", e, exc_info=True)
        raise HTTPException(
            status_code=400,
            detail=f"Error de integridad (municipio duplicado): {str(e.orig)}"
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