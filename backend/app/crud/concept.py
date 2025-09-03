from sqlalchemy.future import select
from uuid import UUID
from app.models.concept import Concept, ConceptTypeEnum
from app.schemas.concept import ConceptCreate, ConceptUpdate, ConceptPatch
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from fastapi import HTTPException, status
from app.utils.audit import log_action
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
import logging
from sqlalchemy import func
from typing import Optional
from app.utils.audit_level import get_audit_level
from app.models.account import Account
from sqlalchemy.orm import selectinload, joinedload

logger = logging.getLogger(__name__)

async def create_concept(db: AsyncSession, concept_in: ConceptCreate, user_id: UUID):
    try:
        concept = Concept(**concept_in.model_dump(), user_id=user_id)
        db.add(concept)
        await db.flush()
        
        log = None
        description = f"Concepto creado: {concept.name} (id={concept.id}, code={concept.code})"
        audit_level = await get_audit_level(db)
        if audit_level > 1:
            log = await log_action(
                db, 
                action="CREATE", 
                entity="Concept", 
                entity_id=concept.id,
                description=description,
                user_id=user_id
            )
            
        return concept, log
        
    except Exception as e:
        logger.exception("Error al crear el concepto")
        raise

async def get_concepts(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    active: Optional[bool] = None,
    user_id: Optional[UUID] = None,
) -> dict:
    try:
        # ✅ Cargar relaciones con las cuentas
        query = select(Concept).options(
            joinedload(Concept.debit_account),
            joinedload(Concept.credit_account)
        )
        
        if search:
            query = query.where(Concept.name.ilike(f"%{search}%"))
        if active is not None:
            query = query.where(Concept.active == active)

        # Consulta para el total
        total_query = select(func.count()).select_from(Concept)
        if search:
            total_query = total_query.where(Concept.name.ilike(f"%{search}%"))
        if active is not None:
            total_query = total_query.where(Concept.active == active)
            
        total_result = await db.execute(total_query)
        total = total_result.scalar_one()

        result = await db.execute(query.offset(skip).limit(limit).order_by(Concept.name))
        concepts = result.scalars().unique().all()
        
        # ✅ Devolver el enum completo
        concept_type_enum = {item.name: item.value for item in ConceptTypeEnum}
        
        audit_level = await get_audit_level(db)
        if audit_level > 2 and user_id:
            await log_action(
                db, action="GETALL", entity="Concept",
                description=f"Consulta de conceptos - search='{search}', active={active}",
                user_id=user_id
            )

        return {
            "total": total, 
            "items": concepts,
            "concept_type_enum": concept_type_enum
        }
        
    except Exception as e:
        await db.rollback()
        logger.exception("Error en get_concepts")
        raise

async def get_concept_by_id(
    db: AsyncSession,
    concept_id: UUID,
    user_id: UUID = None
) -> Concept:
    try:
        # ✅ Cargar relaciones con las cuentas
        query = select(Concept).options(
            joinedload(Concept.debit_account),
            joinedload(Concept.credit_account)
        ).where(Concept.id == concept_id)
        
        result = await db.execute(query)
        concept = result.scalars().first()

        if not concept:
            logger.warning(f"[GET_CONCEPT_BY_ID] Concepto no encontrado: {concept_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Concepto con ID {concept_id} no encontrado"
            )
            
        audit_level = await get_audit_level(db)
        if audit_level > 2 and user_id:
            await log_action(
                db,
                action="GETID",
                entity="Concept",
                entity_id=concept.id,
                description=f"Consultó el concepto: {concept.name}",
                user_id=user_id
            )

        return concept

    except SQLAlchemyError as e:
        await db.rollback()
        logger.error(f"[GET_CONCEPT_BY_ID] Error al consultar el concepto {concept_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al consultar el concepto"
        )
    except Exception as e:
        await db.rollback()
        logger.exception(f"[GET_CONCEPT_BY_ID] Error inesperado al consultar el concepto {concept_id}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ocurrió un error inesperado al consultar el concepto"
        )

# UPDATE (PUT = total)
async def update_concept(
    db: AsyncSession,
    concept_id: UUID,
    concept_in: ConceptUpdate,
    user_id: UUID
):
    try:
        # Busca el concepto existente con relaciones
        query = select(Concept).options(
            joinedload(Concept.debit_account),
            joinedload(Concept.credit_account)
        ).where(Concept.id == concept_id)
        
        result = await db.execute(query)
        concept = result.scalars().first()
        
        if not concept:
            logger.info(f"[update_concept] Concepto {concept_id} no encontrado.")
            return None, None

        cambios = []
        
        # Validar unicidad de código si cambia
        if concept.code != concept_in.code:
            existing_code = await db.execute(
                select(Concept).where(Concept.code == concept_in.code, Concept.id != concept_id)
            )
            if existing_code.scalars().first():
                raise HTTPException(
                    status_code=400,
                    detail=f"Ya existe un concepto con el código '{concept_in.code}'."
                )
            cambios.append(f"código: '{concept.code}' → '{concept_in.code}'")
            concept.code = concept_in.code

        # Validar unicidad de nombre si cambia
        if concept.name != concept_in.name:
            existing_name = await db.execute(
                select(Concept).where(Concept.name == concept_in.name, Concept.id != concept_id)
            )
            if existing_name.scalars().first():
                raise HTTPException(
                    status_code=400,
                    detail=f"Ya existe un concepto con el nombre '{concept_in.name}'."
                )
            cambios.append(f"nombre: '{concept.name}' → '{concept_in.name}'")
            concept.name = concept_in.name

        # Otros campos
        if concept.description != concept_in.description:
            cambios.append(f"descripción: '{concept.description}' → '{concept_in.description}'")
            concept.description = concept_in.description
            
        if concept.concept_type != concept_in.concept_type:
            cambios.append(f"tipo: '{concept.concept_type}' → '{concept_in.concept_type}'")
            concept.concept_type = concept_in.concept_type
            
        if concept.debit_account_id != concept_in.debit_account_id:
            cambios.append(f"cuenta débito ID: '{concept.debit_account_id}' → '{concept_in.debit_account_id}'")
            concept.debit_account_id = concept_in.debit_account_id
                       
        if concept.credit_account_id != concept_in.credit_account_id:
            cambios.append(f"cuenta crédito ID: '{concept.credit_account_id}' → '{concept_in.credit_account_id}'")
            concept.credit_account_id = concept_in.credit_account_id
            
        if concept.active != concept_in.active:
            cambios.append(f"activo: {concept.active} → {concept_in.active}")
            concept.active = concept_in.active

        if not cambios:
            logger.info(f"[update_concept] No hubo cambios en el concepto {concept_id}.")
            return concept, None

        concept.updated_at = datetime.utcnow()
        audit_level = await get_audit_level(db)
        if audit_level >= 1 and user_id:
            log = await log_action(
                db,
                action="UPDATE",
                entity="Concept",
                entity_id=concept.id,
                description=f"Cambios en el concepto: {', '.join(cambios)}",
                user_id=user_id,
            )

        await db.flush()
        return concept, log

    except IntegrityError as e:
        await db.rollback()
        logger.error("[update_concept] Error de integridad: %s", e, exc_info=True)
        raise HTTPException(status_code=400, detail="Error de integridad de datos")
    except SQLAlchemyError as e:
        await db.rollback()
        logger.error("[update_concept] Error SQLAlchemy: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Error en la base de datos")
    except Exception as e:
        await db.rollback()
        logger.exception("[update_concept] Error inesperado", exc_info=True)
        raise HTTPException(status_code=500, detail="Error interno del servidor")

async def patch_concept(
    db: AsyncSession,
    concept_id: UUID,
    concept_in: ConceptPatch,
    user_id: UUID
) -> tuple:
    try:
        # Busca el concepto existente con relaciones
        query = select(Concept).options(
            joinedload(Concept.debit_account),
            joinedload(Concept.credit_account)
        ).where(Concept.id == concept_id)
        
        result = await db.execute(query)
        concept = result.scalars().first()
        
        if not concept:
            logger.warning(f"[patch_concept] Concepto {concept_id} no encontrado.")
            return None, None

        data = concept_in.model_dump(exclude_unset=True)
        cambios = []

        for field, value in data.items():
            if hasattr(concept, field):
                old_value = getattr(concept, field)
                if old_value != value:
                    # Validaciones para código y nombre
                    if field == 'code' and value != concept.code:
                        existing = await db.execute(
                            select(Concept).where(Concept.code == value, Concept.id != concept_id)
                        )
                        if existing.scalars().first():
                            raise HTTPException(status_code=400, detail=f"Código '{value}' ya existe")
                    
                    if field == 'name' and value != concept.name:
                        existing = await db.execute(
                            select(Concept).where(Concept.name == value, Concept.id != concept_id)
                        )
                        if existing.scalars().first():
                            raise HTTPException(status_code=400, detail=f"Nombre '{value}' ya existe")
                    
                    cambios.append(f"{field}: '{old_value}' → '{value}'")
                    setattr(concept, field, value)

        if not cambios:
            logger.info(f"[patch_concept] No hubo cambios en el concepto {concept_id}.")
            return concept, None

        concept.updated_at = datetime.utcnow()
        audit_level = await get_audit_level(db)
        if audit_level >= 1 and user_id:
            log = await log_action(
                db,
                action="PATCH",
                entity="Concept",
                entity_id=concept.id,
                description=f"Actualización parcial: {', '.join(cambios)}",
                user_id=user_id,
            )

        await db.flush()
        return concept, log

    except IntegrityError as e:
        await db.rollback()
        logger.error("[patch_concept] Error de integridad: %s", e, exc_info=True)
        raise HTTPException(status_code=400, detail="Error de integridad de datos")
    except SQLAlchemyError as e:
        await db.rollback()
        logger.error("[patch_concept] Error SQLAlchemy: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Error en la base de datos")
    except Exception as e:
        await db.rollback()
        logger.exception("[patch_concept] Error inesperado", exc_info=True)
        raise HTTPException(status_code=500, detail="Error interno del servidor")