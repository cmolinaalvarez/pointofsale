# app/crud/third_party.py
from __future__ import annotations

import logging
from uuid import UUID
from typing import Optional
from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.third_party import ThirdParty
from app.schemas.third_party import ThirdPartyCreate, ThirdPartyUpdate, ThirdPartyPatch
from app.utils.audit_level import get_audit_level
from app.utils.audit import log_action

logger = logging.getLogger(__name__)


# ==============================
# CREATE
# ==============================
async def create_third_party(db: AsyncSession, third_party_in: ThirdPartyCreate, user_id: UUID):
    try:
        third_party = ThirdParty(**third_party_in.model_dump(), user_id=user_id)
        db.add(third_party)
        await db.flush()  # obtiene el id
    except Exception:
        logger.exception("Error al crear el tercero")
        raise

    log = None
    try:
        description = (
            f"Tercero creado: {third_party.name} "
            f"(id={third_party.id}, active={third_party.active})"
        )
        audit_level = await get_audit_level(db)
        if audit_level > 1:
            log = await log_action(
                db,
                action="CREATE",
                entity="ThirdParty",
                entity_id=third_party.id,
                description=description,
                user_id=third_party.user_id,
            )
    except Exception:
        logger.exception("Error al crear el log de auditoría (ThirdParty/CREATE)")
        raise

    return third_party, log


# ==============================
# GET ALL (paginado + filtros)
# ==============================
async def get_third_parties(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    active: Optional[bool] = None,
    user_id: Optional[UUID] = None,
) -> dict:
    """
    Lista terceros con búsqueda opcional por nombre/código/barcode y filtro por 'active'.
    """
    try:
        query = select(ThirdParty)

        if search:
            like = f"%{search}%"
            query = query.where(
                (ThirdParty.name.ilike(like)) |
                (ThirdParty.code.ilike(like)) |
                (ThirdParty.barcode.ilike(like))
            )
        if active is not None:
            query = query.where(ThirdParty.active == active)

        total_query = select(func.count()).select_from(query.subquery())
        total = (await db.execute(total_query)).scalar_one()

        result = await db.execute(
            query.order_by(ThirdParty.name).offset(skip).limit(limit)
        )
        third_partys = result.scalars().all()

        audit_level = await get_audit_level(db)
        if audit_level > 2 and user_id:
            await log_action(
                db,
                action="GETALL",
                entity="ThirdParty",
                description=f"Consulta de terceros - search='{search}', active={active}, skip={skip}, limit={limit}",
                user_id=user_id,
            )

        return {"total": total, "items": third_partys}

    except SQLAlchemyError:
        await db.rollback()
        logger.exception("Error de base de datos en get_third_parties")
        raise
    except Exception:
        await db.rollback()
        logger.exception("Error inesperado en get_third_parties")
        raise


# ==============================
# GET BY ID
# ==============================
async def get_third_party_by_id(
    db: AsyncSession,
    third_party_id: UUID,
    user_id: Optional[UUID] = None,
) -> ThirdParty:
    """
    Recupera un tercero por UUID y, si corresponde, registra auditoría.
    """
    try:
        result = await db.execute(select(ThirdParty).where(ThirdParty.id == third_party_id))
        third_party = result.scalars().first()

        if not third_party:
            logger.warning(f"[GET_PRODUCT_BY_ID] ThirdPartyo no encontrado: {third_party_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tercero con ID {third_party_id} no encontrado",
            )

        audit_level = await get_audit_level(db)
        if audit_level > 2 and user_id:
            await log_action(
                db,
                action="GETID",
                entity="ThirdParty",
                entity_id=third_party.id,
                description=f"Consultó el third_partyo: {third_party.name} ({third_party.email})",
                user_id=user_id,
            )
        # si log_action hace flush interno no hace falta aquí
        return third_party

    except SQLAlchemyError as e:
        await db.rollback()
        logger.error(f"[GET_THIRD_PARTY_BY_ID] Error al consultar {third_party_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error al consultar el third_partyo")
    except Exception as e:
        await db.rollback()
        logger.exception(f"[GET_THIRD_PARTY_BY_ID] Error inesperado: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Ocurrió un error inesperado")


# ==============================
# UPDATE (PUT)
# ==============================
async def update_third_party(
    db: AsyncSession,
    third_party_id: UUID,
    third_party_in: ThirdPartyUpdate,
    user_id: UUID,
):
    """
    Reemplaza (PUT) los campos del tercero e intenta registrar auditoría.

    Semántica de PUT vs PATCH:
      - PUT normalmente implica reemplazo completo del recurso; se espera
        que el payload contenga todos los campos "requeridos".
      - PATCH aplica cambios parciales (solo los enviados).

    Flujo de esta función:
      1) Buscar el 'ThirdParty' por ID; si no existe, termina con (None, None).
      2) Validar unicidad de campos sensibles (aquí: NIT), *solo si cambian*,
         para evitar consultas innecesarias y condiciones de carrera básicas.
      3) Aplicar los cambios con una función local `_set` que:
           - compara old vs new para registrar un listado de cambios humanos,
           - y solo setea si realmente cambió (evita writes vacíos).
      4) Actualizar 'updated_at'.
      5) Consultar 'audit_level' usando 'no_autoflush' para evitar que el ORM
         intente flushear antes de tiempo (especialmente importante si hay
         objetos “sucios” y restricciones NOT NULL/UNIQUE).
      6) Registrar auditoría si corresponde (nivel >= 1).
      7) 'flush()' para emitir el UPDATE sin cerrar la transacción
         (el commit/rollback suele hacerse en el router o capa superior).
      8) Manejo robusto de errores con rollback.

    Retorno:
      - (entidad_actualizada, registro_auditoría | None)
      - o (None, None) si no se encontró el ID.
    """

    try:
        # 1) Buscar el registro por su ID
        result = await db.execute(
            select(ThirdParty).where(ThirdParty.id == third_party_id)
        )
        third_party = result.scalars().first()
        if not third_party:
            logger.info(f"[update_third_party] tercero {third_party_id} no encontrado.")
            return None, None

        cambios: list[str] = []

        # 2) Validaciones de unicidad CONDICIONALES
        if third_party_in.nit != third_party.nit:
            exists_nit = await db.execute(
                select(ThirdParty.id).where(
                    ThirdParty.nit == third_party_in.nit,
                    ThirdParty.id != third_party_id
                )
            )
            if exists_nit.first():
                raise HTTPException(
                    status_code=400,
                    detail="El nit ya está en uso por otro tercero."
                )

        if third_party_in.name != third_party.name:
            exists_name = await db.execute(
                select(ThirdParty.id).where(
                    ThirdParty.name == third_party_in.name,
                    ThirdParty.id != third_party_id
                )
            )
            if exists_name.first():
                raise HTTPException(
                    status_code=400,
                    detail="El nombre ya está en uso por otro tercero."
                )

        # 3) Helper para aplicar cambios y registrar difs
        def _set(attr: str, new_val):
            old_val = getattr(third_party, attr)
            if old_val != new_val:
                cambios.append(f"{attr}: '{old_val}' → '{new_val}'")
                setattr(third_party, attr, new_val)

        # 4) Aplicación de cambios (PUT)
        _set("name", third_party_in.name)
        _set("third_party_type", third_party_in.third_party_type)
        _set("person_type", third_party_in.person_type)
        _set("contact_name", third_party_in.contact_name)
        _set("phone", third_party_in.phone)
        _set("email", third_party_in.email)
        _set("address", third_party_in.address)
        _set("municipality_id", third_party_in.municipality_id)
        _set("division_id", third_party_in.division_id)
        _set("country_id", third_party_in.country_id)
        _set("nit", third_party_in.nit)
        _set("active", third_party_in.active)

        if not cambios:
            logger.info(f"[update_third_party] No hubo cambios en el tercero {third_party_id}.")
            return third_party, None

        # 5) Timestamp de actualización
        third_party.updated_at = datetime.utcnow()

        # 6) Auditoría sin autoflush (⚠️ usar 'with', no 'async with')
        audit = None
        with db.no_autoflush:
            audit_level = await get_audit_level(db)

        if audit_level >= 1 and user_id:
            audit = await log_action(
                db,
                action="UPDATE",
                entity="ThirdParty",
                entity_id=third_party.id,
                description=f"Cambios en tercero: {', '.join(cambios)}",
                user_id=user_id,
            )

        # 7) Emitir el UPDATE
        await db.flush()

        logger.info(
            f"[update_third_party] Tercero {third_party_id} actualizado por usuario {user_id}."
        )

        # 8) Retorno
        return third_party, audit

    except IntegrityError as e:
        await db.rollback()
        logger.error("[update_third_party] Error de integridad: %s", e, exc_info=True)
        raise HTTPException(
            status_code=400,
            detail="Error de integridad de datos: " + str(e.orig)
        )

    except SQLAlchemyError as e:
        await db.rollback()
        logger.error("[update_third_party] Error SQLAlchemy: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Error en la base de datos")

    except Exception as e:
        await db.rollback()
        logger.exception("[update_third_party] Error inesperado", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


# ==============================
# PATCH (parcial)
# ==============================
async def patch_third_party(
    db: AsyncSession,
    third_party_id: UUID,
    third_party_in: ThirdPartyPatch,
    user_id: UUID,
):
    """
    Actualización parcial de un 'ThirdParty'.
    """

    try:
        # 1) Buscar el registro existente
        result = await db.execute(
            select(ThirdParty).where(ThirdParty.id == third_party_id)
        )
        third_party = result.scalars().first()

        if not third_party:
            logger.warning(f"[patch_third_party] Tercero {third_party_id} no encontrado.")
            return None, None

        # 2) Tomar solo campos enviados
        data = third_party_in.model_dump(exclude_unset=True)

        cambios: list[str] = []

        # 3) Unicidad condicional
        if "nit" in data and data["nit"] != third_party.nit:
            exists_nit = await db.execute(
                select(ThirdParty.id).where(
                    ThirdParty.nit == data["nit"],
                    ThirdParty.id != third_party_id
                )
            )
            if exists_nit.first():
                raise HTTPException(
                    status_code=400,
                    detail="El nit ya está en uso por otro tercero."
                )

        # 4) Aplicar cambios campo a campo
        for field, value in data.items():
            if hasattr(third_party, field):
                old_value = getattr(third_party, field)
                if old_value != value:
                    cambios.append(f"{field}: '{old_value}' → '{value}'")
                    setattr(third_party, field, value)
            else:
                logger.debug(f"[patch_third_party] Campo ignorado (no existe en modelo): {field}")

        if not cambios:
            logger.info(f"[patch_third_party] No hubo cambios en el tercero {third_party_id}.")
            return third_party, None

        # 5) Timestamp
        third_party.updated_at = datetime.utcnow()

        # 6) Auditoría sin autoflush (⚠️ usar 'with', no 'async with')
        audit = None
        with db.no_autoflush:
            audit_level = await get_audit_level(db)

        if audit_level >= 1 and user_id:
            audit = await log_action(
                db,
                action="PATCH",
                entity="ThirdParty",
                entity_id=third_party.id,
                description=f"Actualización parcial: {', '.join(cambios)}",
                user_id=user_id,
            )

        # 7) Emitir UPDATE
        await db.flush()

        logger.info(
            f"[patch_third_party] Tercero {third_party_id} parcheado por usuario {user_id}. Cambios: {cambios}"
        )

        return third_party, audit

    except IntegrityError as e:
        await db.rollback()
        logger.error("[patch_third_party] Error de integridad: %s", e, exc_info=True)
        raise HTTPException(
            status_code=400,
            detail="Error de integridad de datos: " + str(e.orig)
        )

    except SQLAlchemyError as e:
        await db.rollback()
        logger.error("[patch_third_party] Error SQLAlchemy: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Error en la base de datos")

    except Exception as e:
        await db.rollback()
        logger.exception("[patch_third_party] Error inesperado", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")
