# app/crud/stock.py
from __future__ import annotations

from typing import Optional, List, Tuple
from uuid import UUID
from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import selectinload

from app.models.stock import Stock
from app.models.audit_log import AuditLog  # por si log_action lo usa
from app.schemas.stock import StockCreate, StockUpdate, StockPatch
from app.utils.audit import log_action
from app.utils.audit_level import get_audit_level

import logging
logger = logging.getLogger(__name__)


# =========================
# CREATE (POST)
# =========================
async def create_stock(db: AsyncSession, stock_in: StockCreate, user_id: UUID) -> Tuple[Stock, Optional[AuditLog]]:
    """
    Crea un registro de stock. Valida unicidad por (product_id, warehouse_id).
    Genera log de auditoría según nivel configurado.
    """
    try:
        # Valida unicidad (product_id, warehouse_id)
        pair_stmt = select(Stock.id).where(
            Stock.product_id == stock_in.product_id,
            Stock.warehouse_id == stock_in.warehouse_id,
        )
        if (await db.execute(pair_stmt)).first():
            raise HTTPException(
                status_code=400,
                detail="Ya existe un registro de stock para ese producto y bodega."
            )

        stock = Stock(**stock_in.model_dump(exclude_unset=True), user_id=user_id)
        db.add(stock)
        await db.flush()  # asegura stock.id

        audit_level = await get_audit_level(db)
        log = None
        if audit_level >= 1 and user_id:
            desc = f"Stock creado: product={stock.product_id}, warehouse={stock.warehouse_id}, qty={getattr(stock,'quantity', None)}"
            log = await log_action(
                db,
                action="CREATE",
                entity="Stock",
                entity_id=stock.id,
                description=desc,
                user_id=user_id,
            )

        await db.commit()
        await db.refresh(stock)
        return stock, log

    except HTTPException:
        await db.rollback()
        raise
    except IntegrityError as e:
        await db.rollback()
        logger.error("[create_stock] Error de integridad: %s", e, exc_info=True)
        raise HTTPException(status_code=400, detail="Error de integridad: " + str(e.orig))
    except SQLAlchemyError as e:
        await db.rollback()
        logger.error("[create_stock] Error SQLAlchemy: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Error en la base de datos")
    except Exception as e:
        await db.rollback()
        logger.exception("[create_stock] Error inesperado", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error interno: {e}")


# =========================
# GET LIST (paginado + filtros)
# =========================
async def get_stocks(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100,
    product_id: Optional[UUID] = None,
    warehouse_id: Optional[UUID] = None,
    active: Optional[bool] = None,
    user_id: Optional[UUID] = None,
) -> dict:
    """
    Lista stocks con filtros opcionales y auditoría condicional.
    """
    try:
        base = select(Stock)

        if product_id:
            base = base.where(Stock.product_id == product_id)
        if warehouse_id:
            base = base.where(Stock.warehouse_id == warehouse_id)
        if active is not None:
            base = base.where(Stock.active == active)

        # total
        count_stmt = select(func.count(Stock.id))
        if product_id or warehouse_id or active is not None:
            # Replicar filtros en el count
            if product_id:
                count_stmt = count_stmt.where(Stock.product_id == product_id)
            if warehouse_id:
                count_stmt = count_stmt.where(Stock.warehouse_id == warehouse_id)
            if active is not None:
                count_stmt = count_stmt.where(Stock.active == active)

        total = (await db.execute(count_stmt)).scalar_one()

        # items
        stmt = base.order_by(Stock.created_at.desc()).offset(skip).limit(limit)
        res = await db.execute(stmt)
        items = list(res.scalars().all())

        # Auditoría (opcional)
        audit_level = await get_audit_level(db)
        if audit_level > 2 and user_id:
            await log_action(
                db,
                action="GETALL",
                entity="Stock",
                description=f"Consulta stock - product_id={product_id}, warehouse_id={warehouse_id}, active={active}, skip={skip}, limit={limit}",
                user_id=user_id,
            )
            await db.commit()  # persistir log

        return {"total": total, "items": items}

    except SQLAlchemyError as e:
        await db.rollback()
        logger.error("[get_stocks] Error SQLAlchemy: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Error en la base de datos")
    except Exception as e:
        await db.rollback()
        logger.exception("[get_stocks] Error inesperado", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error interno: {e}")


# =========================
# GET BY ID
# =========================
async def get_stock_by_id(
    db: AsyncSession,
    stock_id: UUID,
    user_id: Optional[UUID] = None,
    audit_stock: bool = True
) -> Stock:
    """
    Recupera un stock por ID. Registra auditoría si el nivel lo requiere.
    """
    try:
        res = await db.execute(select(Stock).where(Stock.id == stock_id))
        stock = res.scalars().first()
        if not stock:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Stock no encontrado")

        audit_level = await get_audit_level(db)
        if audit_level > 2 and user_id:
            await log_action(
                db,
                action="GETID",
                entity="Stock",
                entity_id=stock.id,
                description=f"Consultó stock: product={stock.product_id}, warehouse={stock.warehouse_id}",
                user_id=user_id,
            )
            await db.commit()  # persistir log

        return stock

    except HTTPException:
        raise
    except SQLAlchemyError as e:
        await db.rollback()
        logger.error("[get_stock_by_id] Error SQLAlchemy: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Error en la base de datos")
    except Exception as e:
        await db.rollback()
        logger.exception("[get_stock_by_id] Error inesperado", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error interno: {e}")


# =========================
# UPDATE (PUT / total)
# =========================
async def update_stock(
    db: AsyncSession,
    stock_id: UUID,
    stock_in: StockUpdate,
    user_id: UUID,
) -> Tuple[Optional[Stock], Optional[AuditLog]]:
    """
    Reemplaza los campos de un stock y registra auditoría.
    Valida unicidad (product_id, warehouse_id) si cambian.
    Retorna (stock_actualizado, log) o (None, None) si no existe.
    """
    try:
        print("****************************************************************")
        print("**********************stock_id:*******************************",stock_id)
        print("****************************************************************")
        print("****************************************************************")
        print("**********************stock_in:*******************************",stock_in)
        print("****************************************************************")
        print("****************************************************************")
        print("**********************user_id:*******************************",user_id)
        print("****************************************************************")
        res = await db.execute(select(Stock).where(Stock.id == stock_id))
        stock = res.scalars().first()
        if not stock:
            logger.info(f"[update_stock] Stock {stock_id} no encontrado.")
            return None, None

        cambios: List[str] = []

        def _set(attr: str, new_val):
            old_val = getattr(stock, attr)
            if old_val != new_val:
                cambios.append(f"{attr}: '{old_val}' → '{new_val}'")
                setattr(stock, attr, new_val)

        # Aplica cambios (ajusta a los campos reales de tu modelo)
        _set("product_id", stock_in.product_id)
        _set("warehouse_id", stock_in.warehouse_id)
        if hasattr(stock_in, "quantity"):
            _set("quantity", stock_in.quantity)
        if hasattr(stock_in, "reserved"):
            _set("reserved", stock_in.reserved)
        if hasattr(stock_in, "min_stock"):
            _set("min_stock", stock_in.min_stock)
        if hasattr(stock_in, "max_stock"):
            _set("max_stock", stock_in.max_stock)
        if hasattr(stock_in, "active"):
            _set("active", stock_in.active)

        # Unicidad (product_id, warehouse_id)
        pair_stmt = select(Stock.id).where(
            Stock.product_id == stock.product_id,
            Stock.warehouse_id == stock.warehouse_id,
            Stock.id != stock.id,
        )
        if (await db.execute(pair_stmt)).first():
            raise HTTPException(
                status_code=400,
                detail="Ya existe un registro de stock para ese producto y bodega."
            )

        if not cambios:
            logger.info(f"[update_stock] Sin cambios para {stock_id}.")
            return stock, None

        stock.updated_at = datetime.utcnow()

        audit_level = await get_audit_level(db)
        log = None
        if audit_level >= 1 and user_id:
            log = await log_action(
                db,
                action="UPDATE",
                entity="Stock",
                entity_id=stock.id,
                description=f"Cambios en Stock: {', '.join(cambios)}",
                user_id=user_id,
            )

        await db.flush()
        await db.commit()
        await db.refresh(stock)
        return stock, log

    except HTTPException:
        await db.rollback()
        raise
    except IntegrityError as e:
        await db.rollback()
        logger.error("[update_stock] Error de integridad: %s", e, exc_info=True)
        raise HTTPException(status_code=400, detail="Error de integridad: " + str(e.orig))
    except SQLAlchemyError as e:
        await db.rollback()
        logger.error("[update_stock] Error SQLAlchemy: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Error en la base de datos")
    except Exception as e:
        await db.rollback()
        logger.exception("[update_stock] Error inesperado", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error interno: {e}")


# =========================
# PATCH (parcial)
# =========================
async def patch_stock(
    db: AsyncSession,
    stock_id: UUID,
    stock_in: StockPatch,
    user_id: UUID,
) -> Tuple[Optional[Stock], Optional[AuditLog]]:
    """
    Actualización parcial del stock con validación de unicidad si cambian
    product_id o warehouse_id. Registra auditoría.
    """
    try:
        res = await db.execute(select(Stock).where(Stock.id == stock_id))
        stock = res.scalars().first()
        if not stock:
            logger.info(f"[patch_stock] Stock {stock_id} no encontrado.")
            return None, None

        data = stock_in.model_dump(exclude_unset=True)
        cambios: List[str] = []

        # Efectivos (para validar unicidad con posibles cambios en el payload)
        new_product_id = data.get("product_id", stock.product_id)
        new_warehouse_id = data.get("warehouse_id", stock.warehouse_id)

        # Validación de unicidad si cambia la pareja
        if (new_product_id, new_warehouse_id) != (stock.product_id, stock.warehouse_id):
            pair_stmt = select(Stock.id).where(
                Stock.product_id == new_product_id,
                Stock.warehouse_id == new_warehouse_id,
                Stock.id != stock.id,
            )
            if (await db.execute(pair_stmt)).first():
                raise HTTPException(
                    status_code=400,
                    detail="Ya existe un registro de stock para ese producto y bodega."
                )

        # Aplicar cambios
        for field, value in data.items():
            if hasattr(stock, field):
                old_value = getattr(stock, field)
                if old_value != value:
                    cambios.append(f"{field}: '{old_value}' → '{value}'")
                    setattr(stock, field, value)

        if not cambios:
            logger.info(f"[patch_stock] Sin cambios para {stock_id}.")
            return stock, None

        stock.updated_at = datetime.utcnow()

        audit_level = await get_audit_level(db)
        log = None
        if audit_level >= 1 and user_id:
            log = await log_action(
                db,
                action="PATCH",
                entity="Stock",
                entity_id=stock.id,
                description=f"Actualización parcial: {', '.join(cambios)}",
                user_id=user_id,
            )

        await db.flush()
        await db.commit()
        await db.refresh(stock)
        return stock, log

    except HTTPException:
        await db.rollback()
        raise
    except IntegrityError as e:
        await db.rollback()
        logger.error("[patch_stock] Error de integridad: %s", e, exc_info=True)
        raise HTTPException(status_code=400, detail="Error de integridad: " + str(e.orig))
    except SQLAlchemyError as e:
        await db.rollback()
        logger.error("[patch_stock] Error SQLAlchemy: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Error en la base de datos")
    except Exception as e:
        await db.rollback()
        logger.exception("[patch_stock] Error inesperado", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error interno: {e}")
