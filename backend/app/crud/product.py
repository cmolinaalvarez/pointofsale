# app/crud/product.py
from __future__ import annotations

import logging
from uuid import UUID
from typing import Optional
from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.product import Product
from app.schemas.product import ProductCreate, ProductUpdate, ProductPatch
from app.utils.audit_level import get_audit_level
from app.utils.audit import log_action

logger = logging.getLogger(__name__)


# ==============================
# CREATE
# ==============================
async def create_product(db: AsyncSession, product_in: ProductCreate, user_id: UUID):
    try:
        product = Product(**product_in.model_dump(), user_id=user_id)
        db.add(product)
        await db.flush()  # obtiene el id
    except Exception:
        logger.exception("Error al crear el producto")
        raise

    log = None
    try:
        description = (
            f"Producto creado: {product.name} "
            f"(id={product.id}, code={product.code}, price={product.price}, active={product.active})"
        )
        audit_level = await get_audit_level(db)
        if audit_level > 1:
            log = await log_action(
                db,
                action="CREATE",
                entity="Product",
                entity_id=product.id,
                description=description,
                user_id=product.user_id,
            )
    except Exception:
        logger.exception("Error al crear el log de auditoría (Product/CREATE)")
        raise

    return product, log


# ==============================
# GET ALL (paginado + filtros)
# ==============================
async def get_products(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    active: Optional[bool] = None,
    user_id: Optional[UUID] = None,
) -> dict:
    """
    Lista productos con búsqueda opcional por nombre/código/barcode y filtro por 'active'.
    """
    try:
        query = select(Product)

        if search:
            like = f"%{search}%"
            query = query.where(
                (Product.name.ilike(like)) |
                (Product.code.ilike(like)) |
                (Product.barcode.ilike(like))
            )
        if active is not None:
            query = query.where(Product.active == active)

        total_query = select(func.count()).select_from(query.subquery())
        total = (await db.execute(total_query)).scalar_one()

        result = await db.execute(
            query.order_by(Product.name).offset(skip).limit(limit)
        )
        products = result.scalars().all()

        audit_level = await get_audit_level(db)
        if audit_level > 2 and user_id:
            await log_action(
                db,
                action="GETALL",
                entity="Product",
                description=f"Consulta productos - search='{search}', active={active}, skip={skip}, limit={limit}",
                user_id=user_id,
            )

        return {"total": total, "items": products}

    except SQLAlchemyError:
        await db.rollback()
        logger.exception("Error de base de datos en get_products")
        raise
    except Exception:
        await db.rollback()
        logger.exception("Error inesperado en get_products")
        raise


# ==============================
# GET BY ID
# ==============================
async def get_product_by_id(
    db: AsyncSession,
    product_id: UUID,
    user_id: Optional[UUID] = None,
) -> Product:
    """
    Recupera un producto por UUID y, si corresponde, registra auditoría.
    """
    try:
        result = await db.execute(select(Product).where(Product.id == product_id))
        product = result.scalars().first()

        if not product:
            logger.warning(f"[GET_PRODUCT_BY_ID] Producto no encontrado: {product_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Producto con ID {product_id} no encontrado",
            )

        audit_level = await get_audit_level(db)
        if audit_level > 2 and user_id:
            await log_action(
                db,
                action="GETID",
                entity="Product",
                entity_id=product.id,
                description=f"Consultó el producto: {product.name} ({product.code})",
                user_id=user_id,
            )
        # si log_action hace flush interno no hace falta aquí
        return product

    except SQLAlchemyError as e:
        await db.rollback()
        logger.error(f"[GET_PRODUCT_BY_ID] Error al consultar {product_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error al consultar el producto")
    except Exception as e:
        await db.rollback()
        logger.exception(f"[GET_PRODUCT_BY_ID] Error inesperado: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Ocurrió un error inesperado")


# ==============================
# UPDATE (PUT)
# ==============================
async def update_product(
    db: AsyncSession,
    product_id: UUID,
    product_in: ProductUpdate,
    user_id: UUID,
):
    """
    Reemplaza los campos del producto y registra cambios en auditoría.
    Retorna (producto_actualizado, log) o (None, None) si no existe.
    """
    try:
        result = await db.execute(select(Product).where(Product.id == product_id))
        product = result.scalars().first()
        if not product:
            logger.info(f"[update_product] Producto {product_id} no encontrado.")
            return None, None

        cambios = []

        # Cambios básicos + validaciones de unicidad donde importa
        def _set(attr: str, new_val):
            old_val = getattr(product, attr)
            if old_val != new_val:
                cambios.append(f"{attr}: '{old_val}' → '{new_val}'")
                setattr(product, attr, new_val)

        # code (único)
        if product.code != product_in.code:
            exists_code = await db.execute(
                select(Product.id).where(Product.code == product_in.code, Product.id != product_id)
            )
            if exists_code.first():
                raise HTTPException(status_code=400, detail="El código ya está en uso por otro producto.")
            _set("code", product_in.code)

        # name (si quieres evitar duplicados por nombre, descomenta la verificación)
        _set("name", product_in.name)
        _set("description", product_in.description)

        _set("category_id", product_in.category_id)
        _set("brand_id", product_in.brand_id)
        _set("unit_id", product_in.unit_id)

        _set("cost", product_in.cost)
        _set("price", product_in.price)
        _set("percent_tax", product_in.percent_tax)

        # barcode (único si viene)
        if product.barcode != product_in.barcode:
            if product_in.barcode:
                exists_bar = await db.execute(
                    select(Product.id).where(Product.barcode == product_in.barcode, Product.id != product_id)
                )
                if exists_bar.first():
                    raise HTTPException(status_code=400, detail="El código de barras ya está en uso por otro producto.")
            _set("barcode", product_in.barcode)

        _set("image_url", product_in.image_url)
        _set("negative_stock", product_in.negative_stock)
        _set("active", product_in.active)

        if not cambios:
            logger.info(f"[update_product] No hubo cambios en el producto {product_id}.")
            return product, None

        product.updated_at = datetime.utcnow()

        audit = None
        audit_level = await get_audit_level(db)
        if audit_level >= 1 and user_id:
            audit = await log_action(
                db,
                action="UPDATE",
                entity="Product",
                entity_id=product.id,
                description=f"Cambios en producto: {', '.join(cambios)}",
                user_id=user_id,
            )

        await db.flush()
        logger.info(f"[update_product] Producto {product_id} actualizado por usuario {user_id}.")
        return product, audit

    except IntegrityError as e:
        await db.rollback()
        logger.error("[update_product] Error de integridad: %s", e, exc_info=True)
        raise HTTPException(status_code=400, detail="Error de integridad de datos: " + str(e.orig))
    except SQLAlchemyError as e:
        await db.rollback()
        logger.error("[update_product] Error SQLAlchemy: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Error en la base de datos")
    except Exception as e:
        await db.rollback()
        logger.exception("[update_product] Error inesperado", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


# ==============================
# PATCH (parcial)
# ==============================
async def patch_product(
    db: AsyncSession,
    product_id: UUID,
    product_in: ProductPatch,
    user_id: UUID,
):
    """
    Actualización parcial. Valida unicidad de 'code' y 'barcode' si cambian.
    Retorna (producto_actualizado, log) o (None, None) si no existe.
    """
    try:
        result = await db.execute(select(Product).where(Product.id == product_id))
        product = result.scalars().first()
        if not product:
            logger.warning(f"[patch_product] Producto {product_id} no encontrado.")
            return None, None

        data = product_in.model_dump(exclude_unset=True)
        cambios = []

        # Validaciones de unicidad si vienen en el payload
        if "code" in data and data["code"] != product.code:
            exists_code = await db.execute(
                select(Product.id).where(Product.code == data["code"], Product.id != product_id)
            )
            if exists_code.first():
                raise HTTPException(status_code=400, detail="El código ya está en uso por otro producto.")

        if "barcode" in data and data["barcode"] != product.barcode and data["barcode"]:
            exists_bar = await db.execute(
                select(Product.id).where(Product.barcode == data["barcode"], Product.id != product_id)
            )
            if exists_bar.first():
                raise HTTPException(status_code=400, detail="El código de barras ya está en uso por otro producto.")

        for field, value in data.items():
            if hasattr(product, field):
                old_value = getattr(product, field)
                if old_value != value:
                    cambios.append(f"{field}: '{old_value}' → '{value}'")
                    setattr(product, field, value)

        if not cambios:
            logger.info(f"[patch_product] No hubo cambios en el producto {product_id}.")
            return product, None

        product.updated_at = datetime.utcnow()

        audit = None
        audit_level = await get_audit_level(db)
        if audit_level >= 1 and user_id:
            audit = await log_action(
                db,
                action="PATCH",
                entity="Product",
                entity_id=product.id,
                description=f"Actualización parcial: {', '.join(cambios)}",
                user_id=user_id,
            )

        await db.flush()
        logger.info(f"[patch_product] Producto {product_id} parcheado por usuario {user_id}. Cambios: {cambios}")
        return product, audit

    except IntegrityError as e:
        await db.rollback()
        logger.error("[patch_product] Error de integridad: %s", e, exc_info=True)
        raise HTTPException(status_code=400, detail="Error de integridad de datos: " + str(e.orig))
    except SQLAlchemyError as e:
        await db.rollback()
        logger.error("[patch_product] Error SQLAlchemy: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Error en la base de datos")
    except Exception as e:
        await db.rollback()
        logger.exception("[patch_product] Error inesperado", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")
