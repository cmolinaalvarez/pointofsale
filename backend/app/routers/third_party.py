# app/routers/third_partys.py
from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from uuid import UUID
from typing import Optional
from decimal import Decimal, InvalidOperation
from datetime import datetime
import csv
from io import StringIO
import logging

from app.core.security import get_async_db
from app.models.user import User
from app.models.third_party import ThirdParty
from app.schemas.third_party import (
    ThirdPartyCreate, ThirdPartyUpdate, ThirdPartyPatch, ThirdPartyRead, ThirdPartyListResponse
)
from app.crud.third_party import (
    create_third_party, get_third_parties, get_third_party_by_id, update_third_party, patch_third_party
)
from app.utils.audit import log_action
from app.utils.audit_level import get_audit_level
from app.dependencies.auth import get_current_user, require_scopes, current_user_id

logger = logging.getLogger(__name__)

router = APIRouter(tags=["ThirdParties"], dependencies=[Depends(get_current_user)])


# ==============================
# CREATE - POST
# ==============================
@router.post("/", response_model=ThirdPartyRead, status_code=status.HTTP_201_CREATED)
async def create_third_party_endpoint(
    third_party_in: ThirdPartyCreate,
    db: AsyncSession = Depends(get_async_db),
    uid: str = Depends(current_user_id),
):
    try:
        new_third_party, log = await create_third_party(db, third_party_in, uid)
        if log:
            db.add(log)
        await db.commit()
        logger.info(
            "Tercero creado: %s - %s por usuario %s",
            new_third_party.id, new_third_party.name, uid
        )
        return ThirdPartyRead.model_validate(new_third_party)
    except IntegrityError as e:
        await db.rollback()
        logger.error("Integridad al crear tercero: %s", e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error de integridad de datos: " + str(e.orig)
        )
    except SQLAlchemyError as e:
        await db.rollback()
        logger.error("DB al crear tercero: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Error en la base de datos")
    except Exception as e:
        await db.rollback()
        logger.exception("Error interno al crear tercero", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


# ==============================
# GET ALL
# ==============================
@router.get("/", response_model=ThirdPartyListResponse)
async def list_third_parties(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = None,
    active: Optional[bool] = None,
    db: AsyncSession = Depends(get_async_db),
    uid: str = Depends(current_user_id),
):
    try:
        result = await get_third_parties(db, skip, limit, search, active, uid)
        await db.commit()
        return result
    except SQLAlchemyError as e:
        await db.rollback()
        logger.error("DB al listar tercero: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Ocurrió un error en la base de datos")
    except Exception as e:
        await db.rollback()
        logger.exception("Error inesperado al listar tercero", exc_info=True)
        raise HTTPException(status_code=500, detail="Ocurrió un error al obtener los tercero")


# ==============================
# GET BY ID
# ==============================
@router.get("/{third_party_id}", response_model=ThirdPartyRead)
async def read_third_party(
    third_party_id: UUID,
    db: AsyncSession = Depends(get_async_db),
    uid: str = Depends(current_user_id),
):
    try:
        third_party = await get_third_party_by_id(db, third_party_id, uid)
        await db.commit()   # por si hubo auditoría
        return ThirdPartyRead.model_validate(third_party)
    except HTTPException as e:
        await db.rollback()
        logger.error("HTTPException al obtener tercero: %s", e.detail, exc_info=True)
        raise e
    except Exception as e:
        await db.rollback()
        logger.exception("Error inesperado al obtener tercero por ID", exc_info=True)
        raise HTTPException(status_code=500, detail="Ocurrió un error al consultar el tercero")


# ==============================
# UPDATE - PUT
# ==============================
@router.put("/{third_party_id}", response_model=ThirdPartyRead)
async def update_third_party_endpoint(
    third_party_id: UUID,
    third_party_in: ThirdPartyUpdate,
    db: AsyncSession = Depends(get_async_db),
    uid: str = Depends(current_user_id),
):
    try:
        updated, log = await update_third_party(db, third_party_id, third_party_in, uid)
        if not updated:
            raise HTTPException(status_code=404, detail="Tercero no encontrado")
        if log:
            db.add(log)
        await db.commit()
        await db.refresh(updated)
        return ThirdPartyRead.model_validate(updated)
    except IntegrityError as e:
        await db.rollback()
        logger.error("Integridad al actualizar tercero: %s", e, exc_info=True)
        raise HTTPException(status_code=400, detail="Error de integridad de datos.")
    except Exception as e:
        await db.rollback()
        logger.exception("Error inesperado al actualizar tercero", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


# ==============================
# PARTIAL UPDATE - PATCH
# ==============================
@router.patch("/{third_party_id}", response_model=ThirdPartyRead)
async def patch_third_party_endpoint(
    third_party_id: UUID,
    third_party_in: ThirdPartyPatch,
    db: AsyncSession = Depends(get_async_db),
    uid: str = Depends(current_user_id),
):
    try:
        updated, log = await patch_third_party(db, third_party_id, third_party_in, uid)
        if not updated:
            logger.warning("[patch_third_party_endpoint] Tercero %s no encontrado.", third_party_id)
            raise HTTPException(status_code=404, detail="Tercero no encontrado")
        if log:
            db.add(log)
        await db.commit()
        await db.refresh(updated)
        logger.info("[patch_third_party_endpoint] Tercero %s actualizado parcialmente.", third_party_id)
        return ThirdPartyRead.model_validate(updated)
    except IntegrityError as e:
        await db.rollback()
        logger.error("Integridad en PATCH tercero: %s", e, exc_info=True)
        raise HTTPException(status_code=400, detail="Error de integridad de datos.")
    except HTTPException as e:
        await db.rollback()
        raise e
    except Exception as e:
        await db.rollback()
        logger.exception("Error inesperado en PATCH tercero", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


# ==============================
# IMPORT MASSIVE PRODUCTS (CSV)
# ==============================
@router.post("/import", status_code=201)
async def import_third_parties(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_async_db),
    uid: str = Depends(current_user_id),
):
    """
    CSV esperado (headers típicos, todos opcionales salvo code, name, cost, price):
      code,name,description,category_id,brand_id,unit_id,cost,price,percent_tax,barcode,image_url,negative_stock,active
    - UUIDs en *_id
    - cost/price como número o string (se parsea a Decimal)
    - negative_stock/active como true/false/1/0/yes/no/si
    """
    def _to_bool(v) -> bool:
        if v is None:
            return True
        s = str(v).strip().lower()
        return s in ("true", "1", "yes", "si", "y", "t")


    def _to_uuid(v) -> Optional[UUID]:
        if not v:
            return None
        try:
            return UUID(str(v))
        except Exception:
            raise HTTPException(status_code=400, detail=f"UUID inválido: {v}")

    try:
        content = await file.read()
        csv_reader = csv.DictReader(StringIO(content.decode("utf-8")))
        if csv_reader.fieldnames:
            csv_reader.fieldnames = [h.strip().replace('\ufeff', '') for h in csv_reader.fieldnames]
            logger.info("Headers CSV: %s", csv_reader.fieldnames)

        third_partys = []
        count = 0
        for row in csv_reader:
            count += 1
            try:
                third_party = ThirdParty(
                    name=row["name"],
                    person_type=row.get("person_type"),
                    third_party_type=row.get("third_party_type"),
                    contact_name=row.get("contact_name"),
                    phone=row.get("phone"),
                    cell_phone=row.get("cell_phone"),
                    email=row.get("email"),
                    address=row.get("address"),
                    municipality_id=_to_uuid(row.get("municipality_id")),
                    division_id=_to_uuid(row.get("division_id")),
                    country_id=_to_uuid(row.get("country_id")),
                    nit=row.get("nit"),
                    active=_to_bool(row.get("active")) if row.get("active") is not None else True,
                    user_id=uid
                )
                third_partys.append(third_party)
            except KeyError as ke:
                logger.warning("Fila %d: falta columna requerida: %s", count, ke, exc_info=True)
                raise HTTPException(status_code=400, detail=f"Falta columna requerida: {ke}")
            except HTTPException:
                raise
            except Exception as row_err:
                logger.warning("Fila %d con error: %s", count, row_err, exc_info=True)
                raise HTTPException(status_code=400, detail=f"Error en fila {count}: {row_err}")

        if not third_partys:
            raise HTTPException(status_code=400, detail="No se encontraron filas válidas para importar.")

        db.add_all(third_partys)

        audit_level = await get_audit_level(db)
        if audit_level > 1:
            await log_action(
                db,
                action="IMPORT",
                entity="ThirdParty",
                description=f"Importación masiva: {len(third_partys)} terceros importados.",
                user_id=uid,
            )

        await db.commit()
        logger.info("Importación masiva de terceros exitosa. Total: %d", len(third_partys))
        return {"ok": True, "imported": len(third_partys)}

    except IntegrityError as e:
        await db.rollback()
        logger.error("Integridad en importación de terceros: %s", e, exc_info=True)
        raise HTTPException(
            status_code=400,
            detail=f"Error de integridad (tercero duplicado u otra restricción): {str(e.orig)}"
        )
    except HTTPException as e:
        await db.rollback()
        logger.error("HTTPException en importación de terceros: %s", e.detail, exc_info=True)
        raise e
    except Exception as e:
        await db.rollback()
        logger.exception("Error inesperado en importación de terceros", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")