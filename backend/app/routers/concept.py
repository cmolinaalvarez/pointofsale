from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from uuid import UUID
from typing import List, Optional, Dict
from pydantic import BaseModel

from app.schemas.concept import ConceptCreate, ConceptUpdate, ConceptRead, ConceptPatch
from app.crud.concept import create_concept, get_concepts, get_concept_by_id, update_concept, patch_concept
from app.models.user import User
from app.core.security import get_async_db
from app.utils.audit import log_action
import csv
from io import StringIO
from app.utils.audit_level import get_audit_level

from sqlalchemy.orm import selectinload
from app.models.concept import Concept
from backend.app.dependencies.auth import get_current_user, require_scopes, current_user_id
from sqlalchemy import select

import logging
logger = logging.getLogger(__name__)

router = APIRouter(tags=["Concepts"], dependencies=[Depends(get_current_user)])

# ✅ Schema de respuesta para GET ALL
class ConceptListResponse(BaseModel):
    total: int
    items: List[ConceptRead]
    concept_type_enum: Dict[str, str]

    class Config:
        from_attributes = True

# ✅ Schema de respuesta para GET BY ID
class ConceptWithEnumResponse(BaseModel):
    concept: ConceptRead
    concept_type_enum: Dict[str, str]

    class Config:
        from_attributes = True

@router.post("/", response_model=ConceptRead)
async def create_concept_endpoint(concept_in: ConceptCreate, db: AsyncSession = Depends(get_async_db), uid: str = Depends(current_user_id)):
    try:
        new_concept, log = await create_concept(db, concept_in, uid)
        if log:
            db.add(log)
        await db.commit()
        logger.info(f"Concepto creado: {new_concept.id} por usuario {uid}")
        
        # ✅ Cargar relaciones para obtener nombres de cuentas
        from sqlalchemy.orm import selectinload
        from app.models.concept import Concept
        reload_query = select(Concept).options(
            selectinload(Concept.debit_account),
            selectinload(Concept.credit_account)
        ).where(Concept.id == new_concept.id)
        result = await db.execute(reload_query)
        concept_with_relations = result.scalars().first()
        
        # ✅ Convertir a ConceptRead con nombres de cuentas
        concept_data = ConceptRead.model_validate(concept_with_relations)
        concept_data.debit_account_name = concept_with_relations.debit_account.name if concept_with_relations.debit_account else None
        concept_data.credit_account_name = concept_with_relations.credit_account.name if concept_with_relations.credit_account else None
        
        return concept_data
    except Exception as e:
        await db.rollback()
        logger.exception("Error al crear concepto")
        raise HTTPException(status_code=500, detail="Error interno")

@router.get("/", response_model=ConceptListResponse)
async def list_concepts(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = None,
    active: Optional[bool] = None,
    db: AsyncSession = Depends(get_async_db),
    uid: str = Depends(current_user_id),
):
    try:
        result = await get_concepts(db, skip, limit, search, active, uid)
        
        # ✅ Convertir objetos Concept a ConceptRead con nombres de cuentas
        concepts_with_account_names = []
        for concept in result["items"]:
            concept_data = ConceptRead.model_validate(concept)
            concept_data.debit_account_name = concept.debit_account.name if concept.debit_account else None
            concept_data.credit_account_name = concept.credit_account.name if concept.credit_account else None
            concepts_with_account_names.append(concept_data)
        
        await db.commit()
        return {
            "total": result["total"],
            "items": concepts_with_account_names,
            "concept_type_enum": result["concept_type_enum"]
        }
    except Exception as e:
        await db.rollback()
        logger.exception("Error al listar conceptos")
        raise HTTPException(status_code=500, detail="Error al obtener conceptos")

@router.get("/{concept_id}", response_model=ConceptWithEnumResponse)
async def read_concept(concept_id: UUID, db: AsyncSession = Depends(get_async_db), uid: str = Depends(current_user_id)):
    try:
        concept = await get_concept_by_id(db, concept_id, uid)
        
        # ✅ Agregar nombres de cuentas al concepto
        concept_data = ConceptRead.model_validate(concept)
        concept_data.debit_account_name = concept.debit_account.name if concept.debit_account else None
        concept_data.credit_account_name = concept.credit_account.name if concept.credit_account else None
        
        # ✅ Obtener el enum para la respuesta individual
        from app.models.concept import ConceptTypeEnum
        concept_type_enum = {item.name: item.value for item in ConceptTypeEnum}
        
        await db.commit()
        return {
            "concept": concept_data,
            "concept_type_enum": concept_type_enum
        }
    except HTTPException as e:
        await db.rollback()
        raise e
    except Exception as e:
        await db.rollback()
        logger.exception("Error al obtener concepto")
        raise HTTPException(status_code=500, detail="Error al consultar concepto")

@router.put("/{concept_id}", response_model=ConceptRead)
async def update_concept_endpoint(
    concept_id: UUID,
    concept_in: ConceptUpdate,
    db: AsyncSession = Depends(get_async_db),
    uid: str = Depends(current_user_id)
):
    try:
        concept, log = await update_concept(db, concept_id, concept_in, uid)
        if not concept:
            raise HTTPException(status_code=404, detail="Concepto no encontrado")
        
        if log:
            db.add(log)
        
        await db.commit()
        
        # ✅ Recargar con relaciones para obtener nombres actualizados       
        reload_query = select(Concept).options(
            selectinload(Concept.debit_account),
            selectinload(Concept.credit_account)
        ).where(Concept.id == concept_id)
        result = await db.execute(reload_query)
        updated_concept = result.scalars().first()
        
        # ✅ Convertir a ConceptRead con nombres de cuentas
        concept_data = ConceptRead.model_validate(updated_concept)
        concept_data.debit_account_name = updated_concept.debit_account.name if updated_concept.debit_account else None
        concept_data.credit_account_name = updated_concept.credit_account.name if updated_concept.credit_account else None
        
        return concept_data
    except HTTPException as e:
        await db.rollback()
        raise e
    except Exception as e:
        await db.rollback()
        logger.exception("Error al actualizar concepto")
        raise HTTPException(status_code=500, detail="Error interno")

@router.patch("/{concept_id}", response_model=ConceptRead)
async def patch_concept_endpoint(
    concept_id: UUID,
    concept_in: ConceptPatch,
    db: AsyncSession = Depends(get_async_db),
    uid: str = Depends(current_user_id)
):
    try:
        concept, log = await patch_concept(db, concept_id, concept_in, uid)
        if not concept:
            raise HTTPException(status_code=404, detail="Concepto no encontrado")
        
        if log:
            db.add(log)
        
        await db.commit()
        
        # ✅ Recargar con relaciones para obtener nombres actualizados
        
        reload_query = select(Concept).options(
            selectinload(Concept.debit_account),
            selectinload(Concept.credit_account)
        ).where(Concept.id == concept_id)
        result = await db.execute(reload_query)
        updated_concept = result.scalars().first()
        
        # ✅ Convertir a ConceptRead con nombres de cuentas
        concept_data = ConceptRead.model_validate(updated_concept)
        concept_data.debit_account_name = updated_concept.debit_account.name if updated_concept.debit_account else None
        concept_data.credit_account_name = updated_concept.credit_account.name if updated_concept.credit_account else None
        
        return concept_data
    except HTTPException as e:
        await db.rollback()
        raise e
    except Exception as e:
        await db.rollback()
        logger.exception("Error al actualizar parcialmente concepto")
        raise HTTPException(status_code=500, detail="Error interno")

# ==============================
# IMPORT MASSIVE BRANDS
# ==============================
@router.post("/import", status_code=201)
async def import_concepts(
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
        concepts = []
        user_id = uid
        count = 0
        for row in csv_reader:
            try:
                concept = Concept(
                    code=row["code"],
                    name=row["name"],
                    description=row.get("description", ""),
                    debit=row["debit"],
                    debit_account_id=row["debit_account_id"],
                    credit=row["credit"],
                    credit_account_id=row["credit_account_id"],                    
                    active=row.get("active", "true").lower() in ("true", "1", "yes", "si"),
                    user_id=uid
                )
                concepts.append(concept)
                count += 1
            except Exception as row_err:
                logger.warning(
                    "Fila con error en importación de conceptos (fila %d): %s", count + 1, row_err, exc_info=True
                )
                # Si prefieres abortar la importación ante fila errónea, lanza raise aquí

        if not concepts:
            logger.warning("No se encontraron filas válidas para importar en el archivo CSV.")
            raise HTTPException(
                status_code=400,
                detail="No se encontraron filas válidas para importar."
            )
            
        db.add_all(concepts)        
        audit_level = await get_audit_level(db)    # Decidir si registrar el log según el nivel
        if audit_level > 1 and user_id:        
            await log_action(
                db,
                action="IMPORT",
                entity="Concept",
                description=f"Importación masiva: {len(concepts)} conceptos importados.",
                user_id=user_id
            )
        await db.commit()
        logger.info("Importación masiva de conceptos exitosa. Total importadas: %d", len(concepts))
        return {"ok": True, "imported": len(concepts)}

    except IntegrityError as e:
        await db.rollback()
        logger.error("Error de integridad en importación masiva: %s", e, exc_info=True)
        raise HTTPException(
            status_code=400,
            detail=f"Error de integridad (concepto duplicada): {str(e.orig)}"
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