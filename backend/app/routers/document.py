from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from uuid import UUID
from typing import List, Optional

from app.schemas.document import (
    DocumentCreate, DocumentUpdate, DocumentRead, DocumentPatch, DocumentImportResult, DocumentListResponse
)
from app.crud.document import (
    create_document, get_documents, get_document_by_id, update_document, patch_document
)
from app.models.user import User
from app.models.document import Document
from app.core.security import get_async_db
from app.utils.audit import log_action
import csv
from io import StringIO
from app.utils.audit_level import get_audit_level
from backend.app.dependencies.auth import get_current_user, require_scopes, current_user_id

import logging
logger = logging.getLogger(__name__)

router = APIRouter(tags=["Documents"], dependencies=[Depends(get_current_user)])
# ==============================
# CREATE - POST
# ==============================
@router.post("/", response_model=DocumentRead)
async def create_document_endpoint(
    document_in: DocumentCreate,
    db: AsyncSession = Depends(get_async_db),
    uid: str = Depends(current_user_id),
):
    try:
        new_document, log = await create_document(db, document_in, uid)
        if log:
            db.add(log)
        await db.commit()
        # Opcional: log de éxito solo aquí (no es obligatorio, pero si quieres monitorear puedes dejarlo)
        logger.info(f"Documento creado exitosamente: {new_document.id} - {new_document.name} por usuario {uid}")
        return DocumentRead.model_validate(new_document)
    except IntegrityError as e:
        await db.rollback()
        logger.error("Error de integridad al crear el documento: %s", e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error de integridad de datos: " + str(e.orig)
        )
    except SQLAlchemyError as e:
        await db.rollback()
        logger.error("Error de SQLAlchemy al crear el documento: %s", e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error en la base de datos"
        )
    except Exception as e:
        await db.rollback()
        logger.exception("Error interno al crear el documento", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno: {str(e)}"
        )

# ==============================
# GET ALL
# ==============================
@router.get("/", response_model=DocumentListResponse)
async def list_documents(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = None,
    active: Optional[bool] = None,
    db: AsyncSession = Depends(get_async_db),
    uid: str = Depends(current_user_id),
):
    try:
        result = await get_documents(db, skip, limit, search, active, uid)
        await db.commit()
        return result
    except SQLAlchemyError as e:
        await db.rollback()
        logger.error("Error de base de datos al listar los documentos: %s", e, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Ocurrió un error en la base de datos al obtener los documentos"
        )
    except Exception as e:
        await db.rollback()
        logger.exception("Error inesperado al listar documentos", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Ocurrió un error al obtener los documentos"
        )

# ==============================
# GET BY ID
# ==============================
@router.get("/{document_id}", response_model=DocumentRead)
async def read_document(
    document_id: UUID,
    db: AsyncSession = Depends(get_async_db),
    uid: str = Depends(current_user_id),
):
    try:
        document = await get_document_by_id(db, document_id, uid)
        await db.commit()   # Registrar la auditoría si la hubo
        return DocumentRead.model_validate(document)
    except HTTPException as e:
        await db.rollback()
        logger.error("HTTPException al obtener el tipo de documento: %s", e.detail, exc_info=True)
        raise e
    except Exception as e:
        await db.rollback()
        logger.exception("Error inesperado al obtener el tipo de documento por ID", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Ocurrió un error al consultar el tipo de documento"
        )
        
# ==============================
# UPDATE - PUT
# ==============================
@router.put("/{document_id}", response_model=DocumentRead)
async def update_document_endpoint(
    document_id: UUID,
    document_in: DocumentUpdate,
    db: AsyncSession = Depends(get_async_db),
    uid: str = Depends(current_user_id),
):
    try:
        updated, log = await update_document(db, document_id, document_in, uid)
        if not updated:
            raise HTTPException(status_code=404, detail="Tipo de documento no encontrado")
        if log:
            db.add(log)
        await db.commit()
        await db.refresh(updated)
        return DocumentRead.model_validate(updated)
    except IntegrityError as e:
        await db.rollback()
        logger.error("Error de integridad al actualizar el tipo de documento: %s", e, exc_info=True)
        raise HTTPException(
            status_code=400,
            detail="Error de integridad (nombre duplicado u otra restricción)."
        )
    except Exception as e:
        await db.rollback()
        logger.exception("Error inesperado al actualizar el tipo de documento", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error interno: {str(e)}"
        )

# ==============================
# PARTIAL UPDATE - PATCH
# ==============================
@router.patch("/{document_id}", response_model=DocumentRead)
async def patch_document_endpoint(
    document_id: UUID,
    document_in: DocumentPatch,
    db: AsyncSession = Depends(get_async_db),
    uid: str = Depends(current_user_id),
):
    try:
        updated, log = await patch_document(db, document_id, document_in, uid)
        if not updated:
            logger.warning(f"[patch_document_endpoint] Tipo de documento {document_id} no encontrado.")
            raise HTTPException(status_code=404, detail="Tipo de documento no encontrado")
        if log:
            db.add(log)
        await db.commit()
        await db.refresh(updated)
        logger.info(f"[patch_document_endpoint] Tipo de documento {document_id} actualizado parcialmente correctamente.")
        return DocumentRead.model_validate(updated)
    except IntegrityError as e:
        await db.rollback()
        logger.error("Error de integridad al actualizar el tipo de documento (PATCH): %s", e, exc_info=True)
        raise HTTPException(
            status_code=400,
            detail="Error de integridad (nombre duplicado u otra restricción)."
        )
    except HTTPException as e:
        await db.rollback()
        logger.error("HTTPException en patch_document_endpoint: %s", e.detail, exc_info=True)
        raise e
    except Exception as e:
        await db.rollback()
        logger.exception("Error inesperado al actualizar tipo de documento (PATCH)", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error interno: {str(e)}"
        )

# ==============================
# IMPORT MASSIVE BRANDS
# ==============================
@router.post("/import", status_code=201)
async def import_documents(
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
        documents = []
        user_id = uid
        count = 0
        for row in csv_reader:
            try:
                document = Document(
                    code=row["code"],
                    name=row["name"],
                    description=row.get("description", ""),
                    prefix=row["prefix"],
                    document_type=row["document_type"],
                    active=row.get("active", "true").lower() in ("true", "1", "yes", "si"),
                    user_id=uid
                )
                documents.append(document)
                count += 1
            except Exception as row_err:
                logger.warning(
                    "Fila con error en importación de tipos de documento (fila %d): %s", count + 1, row_err, exc_info=True
                )
                # Si prefieres abortar la importación ante fila errónea, lanza raise aquí

        if not documents:
            logger.warning("No se encontraron filas válidas para importar en el archivo CSV.")
            raise HTTPException(
                status_code=400,
                detail="No se encontraron filas válidas para importar."
            )
            
        db.add_all(documents)        
        audit_level = await get_audit_level(db)    # Decidir si registrar el log según el nivel
        if audit_level > 1 and user_id:        
            await log_action(
                db,
                action="IMPORT",
                entity="Document",
                description=f"Importación masiva: {len(documents)} categorias importadas.",
                user_id=user_id
            )
        await db.commit()
        logger.info("Importación masiva de tipos de documento exitosa. Total importadas: %d", len(documents))
        return {"ok": True, "imported": len(documents)}

    except IntegrityError as e:
        await db.rollback()
        logger.error("Error de integridad en importación masiva: %s", e, exc_info=True)
        raise HTTPException(
            status_code=400,
            detail=f"Error de integridad (tipo de documento duplicado): {str(e.orig)}"
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