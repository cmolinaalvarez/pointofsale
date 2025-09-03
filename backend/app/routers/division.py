from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from uuid import UUID
from typing import List, Optional

from app.schemas.division import (
    DivisionCreate, DivisionUpdate, DivisionRead, DivisionPatch, DivisionImportResult, DivisionListResponse
)
from app.crud.division import (
    create_division, get_divisions, get_division_by_id, update_division, patch_division
)
from app.models.user import User
from app.models.division import Division
from app.models.country import Country
from app.core.security import get_async_db
from app.utils.audit import log_action
import csv
from io import StringIO
from app.utils.audit_level import get_audit_level
from backend.app.dependencies.auth import get_current_user, require_scopes, current_user_id

import logging
logger = logging.getLogger(__name__)

router = APIRouter(tags=["Divisions"], dependencies=[Depends(get_current_user)])
# ==============================
# CREATE - POST
# ==============================
@router.post("/", response_model=DivisionRead)
async def create_division_endpoint(
    division_in: DivisionCreate,
    db: AsyncSession = Depends(get_async_db),
    uid: str = Depends(current_user_id),
):
    try:
        new_division, log = await create_division(db, division_in, uid)
        if log:
            db.add(log)
        await db.commit()
        # Opcional: log de éxito solo aquí (no es obligatorio, pero si quieres monitorear puedes dejarlo)
        logger.info(f"División creada exitosamente: {new_division.id} - {new_division.name} por usuario {uid}")
        return DivisionRead.model_validate(new_division)
    except IntegrityError as e:
        await db.rollback()
        logger.error("Error de integridad al crear la división: %s", e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error de integridad de datos: " + str(e.orig)
        )
    except SQLAlchemyError as e:
        await db.rollback()
        logger.error("Error de SQLAlchemy al crear división: %s", e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error en la base de datos"
        )
    except Exception as e:
        await db.rollback()
        logger.exception("Error interno al crear división", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno: {str(e)}"
        )

# ==============================
# GET ALL
# ==============================
@router.get("/", response_model=DivisionListResponse)
async def list_divisions(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = None,
    active: Optional[bool] = None,
    db: AsyncSession = Depends(get_async_db),
    uid: str = Depends(current_user_id),
):
    try:
        result = await get_divisions(db, skip, limit, search, active, uid)
        await db.commit()
        return result
    except SQLAlchemyError as e:
        await db.rollback()
        logger.error("Error de base de datos al listar divisións: %s", e, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Ocurrió un error en la base de datos al obtener las divisións"
        )
    except Exception as e:
        await db.rollback()
        logger.exception("Error inesperado al listar divisións", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Ocurrió un error al obtener las divisións"
        )

# ==============================
# GET BY ID
# ==============================
@router.get("/{division_id}", response_model=DivisionRead)
async def read_division(
    division_id: UUID,
    db: AsyncSession = Depends(get_async_db),
    uid: str = Depends(current_user_id),
):
    try:
        division = await get_division_by_id(db, division_id, uid)
        await db.commit()   # Registrar la auditoría si la hubo
        return DivisionRead.model_validate(division)
    except HTTPException as e:
        await db.rollback()
        logger.error("HTTPException al obtener la división: %s", e.detail, exc_info=True)
        raise e
    except Exception as e:
        await db.rollback()
        logger.exception("Error inesperado al obtener la división por ID", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Ocurrió un error al consultar la división"
        )
        
# ==============================
# UPDATE - PUT
# ==============================
@router.put("/{division_id}", response_model=DivisionRead)
async def update_division_endpoint(
    division_id: UUID,
    division_in: DivisionUpdate,
    db: AsyncSession = Depends(get_async_db),
    uid: str = Depends(current_user_id),
):
    try:
        updated, log = await update_division(db, division_id, division_in, uid)
        if not updated:
            raise HTTPException(status_code=404, detail="División no encontrada")
        if log:
            db.add(log)
        await db.commit()
        await db.refresh(updated)
        return DivisionRead.model_validate(updated)
    except IntegrityError as e:
        await db.rollback()
        logger.error("Error de integridad al actualizar división: %s", e, exc_info=True)
        raise HTTPException(
            status_code=400,
            detail="Error de integridad (nombre duplicado u otra restricción)."
        )
    except Exception as e:
        await db.rollback()
        logger.exception("Error inesperado al actualizar división", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error interno: {str(e)}"
        )

# ==============================
# PARTIAL UPDATE - PATCH
# ==============================
@router.patch("/{division_id}", response_model=DivisionRead)
async def patch_division_endpoint(
    division_id: UUID,
    division_in: DivisionPatch,
    db: AsyncSession = Depends(get_async_db),
    uid: str = Depends(current_user_id),
):
    try:
        updated, log = await patch_division(db, division_id, division_in, uid)
        if not updated:
            logger.warning(f"[patch_division_endpoint] División {division_id} no encontrada.")
            raise HTTPException(status_code=404, detail="División no encontrada")
        if log:
            db.add(log)
        await db.commit()
        await db.refresh(updated)
        logger.info(f"[patch_division_endpoint] División {division_id} actualizada parcialmente correctamente.")
        return DivisionRead.model_validate(updated)
    except IntegrityError as e:
        await db.rollback()
        logger.error("Error de integridad al actualizar la división (PATCH): %s", e, exc_info=True)
        raise HTTPException(
            status_code=400,
            detail="Error de integridad (nombre duplicado u otra restricción)."
        )
    except HTTPException as e:
        await db.rollback()
        logger.error("HTTPException en patch_division_endpoint: %s", e.detail, exc_info=True)
        raise e
    except Exception as e:
        await db.rollback()
        logger.exception("Error inesperado al actualizar división (PATCH)", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error interno: {str(e)}"
        )

# ==============================
# IMPORT MASSIVE BRANDS
# ==============================
@router.post("/import", status_code=201)
async def import_divisiones(
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
        divisions = []
        user_id = uid
        count = 0
        for row in csv_reader:
            result = await db.execute(select(Country).where(Country.country_code == row["country_code"]))
            country = result.scalars().first()  
            if country: 
                try:
                    division = Division(
                        code=row["code"],
                        name=row["name"],  
                        country_id=country.id,                  
                        country_code=row["country_code"],        
                        iso_3166_2=row["iso_3166_2"],
                        active=row.get("active", "true").lower() in ("true", "1", "yes", "si"),
                        user_id=uid
                    )
                    divisions.append(division)
                    count += 1
                except Exception as row_err:
                    logger.warning(
                        "Fila con error en importación de divisións (fila %d): %s", count + 1, row_err, exc_info=True
                    )
                    # Si prefieres abortar la importación ante fila errónea, lanza raise aquí
            else:
                logger.warning(
                        "Fila con error en importación de divisións (fila %d): %s", count + 1, row_err, exc_info=True
                    ) 
                raise HTTPException(
                status_code=400,
                detail="La fila no tiene un country_code."
            )              

        if not divisions:
            logger.warning("No se encontraron filas válidas para importar en el archivo CSV.")
            raise HTTPException(
                status_code=400,
                detail="No se encontraron filas válidas para importar."
            )
            
        db.add_all(divisions)        
        audit_level = await get_audit_level(db)    # Decidir si registrar el log según el nivel
        if audit_level > 1 and user_id:        
            await log_action(
                db,
                action="IMPORT",
                entity="Division",
                description=f"Importación masiva: {len(divisions)} divisións importadas.",
                user_id=user_id
            )
        await db.commit()
        logger.info("Importación masiva de división exitosa. Total importadas: %d", len(divisions))
        return {"ok": True, "imported": len(divisions)}

    except IntegrityError as e:
        await db.rollback()
        logger.error("Error de integridad en importación masiva: %s", e, exc_info=True)
        raise HTTPException(
            status_code=400,
            detail=f"Error de integridad (división duplicada): {str(e.orig)}"
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