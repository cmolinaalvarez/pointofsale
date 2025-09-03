from sqlalchemy.future import select
from uuid import UUID
from app.models.document import Document
from app.schemas.document import DocumentCreate, DocumentUpdate, DocumentPatch
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.audit_log import AuditLog
from datetime import datetime
from fastapi import HTTPException
from app.utils.audit import log_action
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from datetime import datetime
import logging  
from sqlalchemy.future import select
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from fastapi import APIRouter,HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import logging
from sqlalchemy.exc import SQLAlchemyError
from app.utils.audit_level import get_audit_level

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/documents", tags=["Ddocuments"])

async def create_document(db: AsyncSession, document_in: DocumentCreate, user_id: UUID):
    try:
        document = Document(**document_in.model_dump(), user_id=user_id)
        db.add(document)
        await db.flush()
    except Exception as e:
        logger.exception("Error al crear el tipo de documento")  # Solo errores
        raise
    log = None
    try:
        description = (
            f"Documento creado: {document.name} "
            f"(id={document.id}, code={document.code}, description={document.description}, description={document.document_type}, active={document.active})"
        )
        audit_level = await get_audit_level(db)    # Decidir si registrar el log según el nivel
        if audit_level > 1:
            log = await log_action(
                db,
                action="CREATE",
                entity="Document",
                entity_id=document.id,
                description=description,
                user_id=document.user_id
            )
    except Exception as e:
        logger.exception("Error al crear el log de auditoría")  # Solo errores
        raise
    print(log)
    return document, log

# GET ALL

async def get_documents(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    active: Optional[bool] = None,
    user_id: Optional[UUID] = None,  # Para auditoría
) -> dict:
    """
    Retorna una lista paginada de tipos de documentos, con soporte para búsqueda por nombre y filtro por estado activo.
    Registra la auditoría si es necesario.
    """
    try:
        query = select(Document)

        if search:
            query = query.where(Document.name.ilike(f"%{search}%"))
        if active is not None:
            query = query.where(Document.active == active)

        # Calcular total de resultados
        total_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(total_query)
        total = total_result.scalar_one()

        # Obtener las tipo de documentos paginadas
        result = await db.execute(
            query.offset(skip).limit(limit).order_by(Document.name)
        )
        documents = result.scalars().all()
        audit_level = await get_audit_level(db)    # Decidir si registrar el log según el nivel
        if audit_level > 2 and user_id:
            await log_action(
                db,
                action="GETALL",
                entity="Document",
                description=f"Consulta de documentos - filtros: search='{search}', active={active}, skip={skip}, limit={limit}",
                user_id=user_id,
            )
            # db.flush()
        return {"total": total, "items": documents}
    except SQLAlchemyError as e:
        await db.rollback()
        logging.exception("Error de base de datos en get_documents", exc_info=True)
        raise  # Puedes relanzar aquí y manejarlo en el endpoint
    except Exception as e:
        await db.rollback()
        logging.exception("Error inesperado en get_documents", exc_info=True)
        raise
  
async def get_document_by_id(
    db: AsyncSession,
    document_id: UUID,
    user_id: UUID = None,  # Permite auditoría solo si hay user_id
    audit_document: bool = True
) -> Document:
    """
    Recupera un documento por su UUID y registra auditoría si se encuentra.

    Args:
        db (AsyncSession): Sesión de base de datos asincrónica.
        document_id (UUID): ID de el tipo de documento a buscar.
        user_id (UUID, opcional): Usuario que realiza la consulta (para registrar auditoría).

    Returns:
        Document: Objeto encontrado.

    Raises:
        HTTPException:
            - 404 si no se encuentra el documento.
            - 500 si ocurre un error de base de datos.
    """
    try:
        result = await db.execute(select(Document).where(Document.id == document_id))
        document = result.scalars().first()
        print("document en get_document_by_id ::::::::::::::",document)
        if not document:
            logger.warning(f"[GET_BRAND_BY_ID] Documento no encontrado: {document_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Documento con ID {document_id} no encontrado"
            )
        if audit_document:    
            audit_level = await get_audit_level(db)    # Decidir si registrar el log según el nivel
            if audit_level > 2 and user_id:
                # Registrar auditoría si hay user_id
                await log_action(
                    db,
                    action="GETID",
                    entity="Document",
                    entity_id=document.id,
                    description=f"Consultó el documento: {document.name}",
                    user_id=user_id
                )
                # No commit aquí, solo flush si log_action lo requiere
                db.flush()
        return document

    except SQLAlchemyError as e:
        await db.rollback()
        logger.error(f"[GET_BRAND_BY_ID] Error al consultar el documento {document_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al consultar el documento"
        )
    except Exception as e:
        await db.rollback()
        logger.exception(f"[GET_BRAND_BY_ID] Error inesperado al consultar el documento {document_id}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ocurrió un error inesperado al consultar el documento"
        )       


# UPDATE (PUT = total)
async def update_document(
    db: AsyncSession,
    document_id: UUID,
    document_in: 'DocumentUpdate',
    user_id: UUID
):
    """
    Actualiza un tipo de documento y construye el log de auditoría.
    - Retorna (document_actualizada, log_de_auditoria)
    - Si no hay cambios, retorna (document, None)
    - Si el tipo de documento no existe, retorna (None, None)
    """
    try:
        # 1. Busca el tipo de documento existente
        result = await db.execute(select(Document).where(Document.id == document_id))
        document = result.scalars().first()
        if not document:
            logger.info(f"[update_document] Documento {document_id} no encontrado.")
            return None, None

        cambios = []
        
        # 1. Detecta y aplica otros cambios
        if document.code != document_in.code:
            cambios.append(f"código: '{document.code}' → '{document_in.code}'")
            document.code = document_in.code

        # 2. Valida unicidad de nombre SOLO si cambia el nombre
        if document.name != document_in.name:
            existing = await db.execute(
                select(Document).where(Document.name == document_in.name, Document.id != document_id)
            )
            if existing.scalars().first():
                logger.warning(f"[update_document] Nombre duplicado: {document_in.name}")
                raise HTTPException(
                    status_code=400,
                    detail=f"Ya existe un tipo de documento con el nombre '{document_in.name}'."
                )
            cambios.append(f"nombre: '{document.name}' → '{document_in.name}'")
            document.name = document_in.name

        # 3. Detecta y aplica otros cambios
        if document.code != document_in.code:
            cambios.append(f"code: '{document.code}' → '{document_in.code}'")
            document.code = document_in.code
        
            # 3. Detecta y aplica otros cambios
        if document.description != document_in.description:
            cambios.append(f"code: '{document.description}' → '{document_in.description}'")
            document.description = document_in.description
        
        if document.active != document_in.active:
            cambios.append(f"activo: {document.active} → {document_in.active}")
            document.active = document_in.active

        # 4. Si no hay cambios, retorna solo el tipo de documento (sin log)
        if not cambios:
            logger.info(f"[update_document] No hubo cambios en el tipo de documento {document_id}.")
            return document, None

        # 5. Actualiza el timestamp
        document.updated_at = datetime.utcnow()
        audit_level = await get_audit_level(db)    # Decidir si registrar el log según el nivel
        if audit_level >= 1 and user_id:
            # 6. Crea el log de auditoría con la descripción de cambios
            log = await log_action(
                db,
                action="UPDATE",
                entity="Document",
                entity_id=document.id,
                description=f"Cambios en el tipo de documento: {', '.join(cambios)}",
                user_id=user_id,
            )

        await db.flush()  # Asegura que ambos cambios estén en la sesión

        logger.info(f"[update_document] tipo de documento {document_id} actualizada por usuario {user_id}.")
        return document, log

    except IntegrityError as e:
        await db.rollback()
        logger.error("[update_document] Error de integridad: %s", e, exc_info=True)
        raise HTTPException(
            status_code=400,
            detail="Error de integridad de datos: " + str(e.orig)
        )
    except SQLAlchemyError as e:
        await db.rollback()
        logger.error("[update_document] Error SQLAlchemy: %s", e, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Error en la base de datos"
        )
    except Exception as e:
        await db.rollback()
        logger.exception("[update_document] Error inesperado", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error interno: {str(e)}"
        )
        
async def patch_document(
    db: AsyncSession,
    document_id: UUID,
    document_in: 'DocumentPatch',
    user_id: UUID  # ¡Para log de auditoría!
) -> tuple:
    """
    Actualiza parcialmente un tipo de documento (PATCH) y registra log de auditoría.
    Retorna (document_actualizado, log_de_auditoria) o (None, None) si no existe.
    """
    try:
         # 1. Busca el tipo de documento existente
        result = await db.execute(select(Document).where(Document.id == document_id))
        document = result.scalars().first()
        if not document:
            logger.warning(f"[patch_document] Documento {document_id} no encontrado.")
            return None, None

        data = document_in.dict(exclude_unset=True)
        cambios = []

        for field, value in data.items():
            if hasattr(document, field):
                old_value = getattr(document, field)
                if old_value != value:
                    cambios.append(f"{field}: '{old_value}' → '{value}'")
                    setattr(document, field, value)

        if not cambios:
            logger.info(f"[patch_document] No hubo cambios en el tipo de documento {document_id}.")
            return document, None

        document.updated_at = datetime.utcnow()
        audit_level = await get_audit_level(db)    # Decidir si registrar el log según el nivel
        if audit_level >= 1 and user_id:
            log = await log_action(
                db,
                action="PATCH",
                entity="Document",
                entity_id=document.id,
                description=f"Actualización parcial: {', '.join(cambios)}",
                user_id=user_id,
            )

        await db.flush()  # Asegura que los cambios y log estén listos para commit

        logger.info(f"[patch_document] tipo de documento {document_id} parcheado por usuario {user_id}. Cambios: {cambios}")
        return document, log

    except IntegrityError as e:
        await db.rollback()
        logger.error("[patch_document] Error de integridad: %s", e, exc_info=True)
        raise HTTPException(
            status_code=400,
            detail="Error de integridad de datos: " + str(e.orig)
        )
    except SQLAlchemyError as e:
        await db.rollback()
        logger.error("[patch_document] Error SQLAlchemy: %s", e, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Error en la base de datos"
        )
    except Exception as e:
        await db.rollback()
        logger.exception("[patch_document] Error inesperado", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error interno: {str(e)}"
        )
