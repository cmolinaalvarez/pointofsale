from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from uuid import UUID
from typing import List, Optional
import csv
from io import StringIO
import time

from app.schemas.payment_term import (
    PaymentTermCreate, PaymentTermUpdate, PaymentTermRead, 
    PaymentTermPatch, PaymentTermImportResult, PaymentTermListResponse
)
from app.crud.payment_term import (
    create_payment_term, get_payment_terms, get_payment_term_by_id, 
    update_payment_term, patch_payment_term, delete_payment_term
)
from app.models.user import User
from app.dependencies.current_user import get_current_user
from app.core.security import get_async_db
from app.utils.audit import log_action
from app.utils.audit_level import get_audit_level

import logging
logger = logging.getLogger(__name__)

router = APIRouter(tags=["PaymentTerms"])

# ==============================
# CREATE - POST
# ==============================
@router.post("/", response_model=PaymentTermRead, status_code=status.HTTP_201_CREATED)
async def create_payment_term_endpoint(
    payment_term_in: PaymentTermCreate,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    """
    Crear un nuevo término de pago
    """
    try:
        new_payment_term, log = await create_payment_term(
            db, payment_term_in.model_dump(), current_user.id
        )
        
        if log:
            db.add(log)
            
        await db.commit()
        await db.refresh(new_payment_term)
        
        logger.info(f"Término de pago creado exitosamente: {new_payment_term.id} - {new_payment_term.name} por usuario {current_user.id}")
        return PaymentTermRead.model_validate(new_payment_term)
        
    except HTTPException:
        await db.rollback()
        raise
    except IntegrityError as e:
        await db.rollback()
        logger.error("Error de integridad al crear término de pago: %s", e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error de integridad de datos: " + str(e.orig)
        )
    except SQLAlchemyError as e:
        await db.rollback()
        logger.error("Error de SQLAlchemy al crear término de pago: %s", e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error en la base de datos"
        )
    except Exception as e:
        await db.rollback()
        logger.exception("Error interno al crear término de pago", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno: {str(e)}"
        )

# ==============================
# GET ALL
# ==============================
@router.get("/", response_model=PaymentTermListResponse)
async def list_payment_terms(
    skip: int = Query(0, ge=0, description="Número de registros a saltar"),
    limit: int = Query(100, ge=1, le=1000, description="Límite de registros por página"),
    search: Optional[str] = Query(None, description="Término de búsqueda"),
    active: Optional[bool] = Query(None, description="Filtrar por estado activo/inactivo"),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    """
    Listar términos de pago con paginación y filtros
    """
    try:
        result = await get_payment_terms(db, skip, limit, search, active, current_user.id)
        await db.commit()
        return result
        
    except SQLAlchemyError as e:
        await db.rollback()
        logger.error("Error de base de datos al listar términos de pago: %s", e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ocurrió un error en la base de datos al obtener los términos de pago"
        )
    except Exception as e:
        await db.rollback()
        logger.exception("Error inesperado al listar términos de pago", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ocurrió un error al obtener los términos de pago"
        )

# ==============================
# GET BY ID
# ==============================
@router.get("/{payment_term_id}", response_model=PaymentTermRead)
async def read_payment_term(
    payment_term_id: UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    """
    Obtener un término de pago por ID
    """
    try:
        payment_term = await get_payment_term_by_id(db, payment_term_id, current_user.id)
        await db.commit()
        return PaymentTermRead.model_validate(payment_term)
        
    except HTTPException as e:
        await db.rollback()
        raise e
    except Exception as e:
        await db.rollback()
        logger.exception("Error inesperado al obtener el término de pago por ID", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ocurrió un error al consultar el término de pago"
        )

# ==============================
# UPDATE - PUT
# ==============================
@router.put("/{payment_term_id}", response_model=PaymentTermRead)
async def update_payment_term_endpoint(
    payment_term_id: UUID,
    payment_term_in: PaymentTermUpdate,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    """
    Actualizar un término de pago
    """
    try:
        updated, log = await update_payment_term(
            db, payment_term_id, payment_term_in.model_dump(), current_user.id
        )
        
        if not updated:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Término de pago no encontrado"
            )
            
        if log:
            db.add(log)
            
        await db.commit()
        await db.refresh(updated)
        
        return PaymentTermRead.model_validate(updated)
        
    except HTTPException:
        await db.rollback()
        raise
    except IntegrityError as e:
        await db.rollback()
        logger.error("Error de integridad al actualizar término de pago: %s", e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error de integridad (código duplicado u otra restricción)."
        )
    except Exception as e:
        await db.rollback()
        logger.exception("Error inesperado al actualizar término de pago", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno: {str(e)}"
        )

# ==============================
# PARTIAL UPDATE - PATCH
# ==============================
@router.patch("/{payment_term_id}", response_model=PaymentTermRead)
async def patch_payment_term_endpoint(
    payment_term_id: UUID,
    payment_term_in: PaymentTermPatch,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    """
    Actualizar parcialmente un término de pago
    """
    try:
        updated, log = await patch_payment_term(
            db, payment_term_id, payment_term_in.model_dump(exclude_unset=True), current_user.id
        )
        
        if not updated:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Término de pago no encontrado"
            )
            
        if log:
            db.add(log)
            
        await db.commit()
        await db.refresh(updated)
        
        logger.info(f"Término de pago {payment_term_id} actualizado parcialmente correctamente.")
        return PaymentTermRead.model_validate(updated)
        
    except HTTPException:
        await db.rollback()
        raise
    except IntegrityError as e:
        await db.rollback()
        logger.error("Error de integridad al actualizar término de pago (PATCH): %s", e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error de integridad (código duplicado u otra restricción)."
        )
    except Exception as e:
        await db.rollback()
        logger.exception("Error inesperado al actualizar término de pago (PATCH)", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno: {str(e)}"
        )

# ==============================
# DELETE
# ==============================
@router.delete("/{payment_term_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_payment_term_endpoint(
    payment_term_id: UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    """
    Eliminar un término de pago
    """
    try:
        deleted = await delete_payment_term(db, payment_term_id, current_user.id)
        
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Término de pago no encontrado"
            )
            
        await db.commit()
        
    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        logger.exception("Error inesperado al eliminar término de pago", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno: {str(e)}"
        )

# ==============================
# IMPORT MASSIVE PAYMENT TERMS
# ==============================
@router.post("/import", response_model=PaymentTermImportResult, status_code=status.HTTP_201_CREATED)
async def import_payment_terms(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    """
    Importar términos de pago desde archivo CSV
    """
    try:
        content = await file.read()
        csv_reader = csv.DictReader(StringIO(content.decode("utf-8")))
        
        # Limpiar headers
        if csv_reader.fieldnames:
            csv_reader.fieldnames = [h.strip().replace('\ufeff', '') for h in csv_reader.fieldnames]
            logger.info(f"Headers después de limpieza: {csv_reader.fieldnames}")
            
        payment_terms = []
        imported_count = 0
        error_count = 0
        errors = []
        
        for row_number, row in enumerate(csv_reader, 1):
            try:
                # Validar y procesar fila
                payment_term_data = {
                    "code": row["code"],
                    "name": row["name"],
                    "description": row.get("description", ""),
                    "net_days": int(row["net_days"]),
                    "discount_percent": float(row["discount_percent"]),
                    "discount_days": int(row["discount_days"]),
                    "basis": row["basis"],
                    "active": row.get("active", "true").lower() in ("true", "1", "yes", "si")
                }
                
                # Crear término de pago
                payment_term = await create_payment_term(db, payment_term_data, current_user.id)
                payment_terms.append(payment_term)
                imported_count += 1
                
            except Exception as row_err:
                error_count += 1
                error_msg = f"Fila {row_number}: {str(row_err)}"
                errors.append(error_msg)
                logger.warning("Fila con error en importación de términos de pago: %s", error_msg, exc_info=True)
        
        # Registrar auditoría de importación
        audit_level = await get_audit_level(db)
        if audit_level > 1:
            await log_action(
                db,
                action="IMPORT",
                entity="PaymentTerm",
                description=f"Importación masiva: {imported_count} términos de pago importados.",
                user_id=current_user.id
            )
            
        await db.commit()
        
        logger.info("Importación masiva de términos de pago exitosa. Total importados: %d", imported_count)
        
        return PaymentTermImportResult(
            total_imported=imported_count,
            total_errors=error_count,
            imported=[pt.id for pt in payment_terms],
            errors=errors
        )
        
    except IntegrityError as e:
        await db.rollback()
        logger.error("Error de integridad en importación masiva: %s", e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error de integridad (término de pago duplicado): {str(e.orig)}"
        )
    except Exception as e:
        await db.rollback()
        logger.exception("Error inesperado en importación masiva", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno: {str(e)}"
        )