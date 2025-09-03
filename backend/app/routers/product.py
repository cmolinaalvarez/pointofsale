# app/routers/products.py
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
from app.models.product import Product
from app.schemas.product import (
    ProductCreate, ProductUpdate, ProductPatch, ProductRead, ProductListResponse
)
from app.crud.product import (
    create_product, get_products, get_product_by_id, update_product, patch_product
)
from app.utils.audit import log_action
from app.utils.audit_level import get_audit_level
from app.dependencies.auth import get_current_user, require_scopes, current_user_id

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Products"], dependencies=[Depends(get_current_user)])


# ==============================
# CREATE - POST
# ==============================
@router.post("/", response_model=ProductRead, status_code=status.HTTP_201_CREATED)
async def create_product_endpoint(
    product_in: ProductCreate,
    db: AsyncSession = Depends(get_async_db),
    uid: str = Depends(current_user_id),
):
    try:
        new_product, log = await create_product(db, product_in, uid)
        if log:
            db.add(log)
        await db.commit()
        logger.info(
            "Producto creado: %s - %s por usuario %s",
            new_product.id, new_product.name, uid
        )
        return ProductRead.model_validate(new_product)
    except IntegrityError as e:
        await db.rollback()
        logger.error("Integridad al crear producto: %s", e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error de integridad de datos: " + str(e.orig)
        )
    except SQLAlchemyError as e:
        await db.rollback()
        logger.error("DB al crear producto: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Error en la base de datos")
    except Exception as e:
        await db.rollback()
        logger.exception("Error interno al crear producto", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


# ==============================
# GET ALL
# ==============================
@router.get("/", response_model=ProductListResponse)
# @require_scope("read:products")  # Comentar temporalmente
async def list_products(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = None,
    active: Optional[bool] = None,
    db: AsyncSession = Depends(get_async_db),  # Usar get_db corregido
    uid: str = Depends(current_user_id),
):
    try:
        result = await get_products(db, skip, limit, search, active, uid)
        await db.commit()
        return result
    except SQLAlchemyError as e:
        await db.rollback()
        logger.error("DB al listar productos: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Ocurrió un error en la base de datos")
    except Exception as e:
        await db.rollback()
        logger.exception("Error inesperado al listar productos", exc_info=True)
        raise HTTPException(status_code=500, detail="Ocurrió un error al obtener los productos")


# ==============================
# GET BY ID
# ==============================
@router.get("/{product_id}", response_model=ProductRead)
async def read_product(
    product_id: UUID,
    db: AsyncSession = Depends(get_async_db),
    uid: str = Depends(current_user_id),
):
    try:
        product = await get_product_by_id(db, product_id, uid)
        await db.commit()   # por si hubo auditoría
        return ProductRead.model_validate(product)
    except HTTPException as e:
        await db.rollback()
        logger.error("HTTPException al obtener producto: %s", e.detail, exc_info=True)
        raise e
    except Exception as e:
        await db.rollback()
        logger.exception("Error inesperado al obtener producto por ID", exc_info=True)
        raise HTTPException(status_code=500, detail="Ocurrió un error al consultar el producto")


# ==============================
# UPDATE - PUT
# ==============================
@router.put("/{product_id}", response_model=ProductRead)
async def update_product_endpoint(
    product_id: UUID,
    product_in: ProductUpdate,
    db: AsyncSession = Depends(get_async_db),
    uid: str = Depends(current_user_id),
):
    try:
        updated, log = await update_product(db, product_id, product_in, uid)
        if not updated:
            raise HTTPException(status_code=404, detail="Producto no encontrado")
        if log:
            db.add(log)
        await db.commit()
        await db.refresh(updated)
        return ProductRead.model_validate(updated)
    except IntegrityError as e:
        await db.rollback()
        logger.error("Integridad al actualizar producto: %s", e, exc_info=True)
        raise HTTPException(status_code=400, detail="Error de integridad de datos.")
    except Exception as e:
        await db.rollback()
        logger.exception("Error inesperado al actualizar producto", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


# ==============================
# PARTIAL UPDATE - PATCH
# ==============================
@router.patch("/{product_id}", response_model=ProductRead)
async def patch_product_endpoint(
    product_id: UUID,
    product_in: ProductPatch,
    db: AsyncSession = Depends(get_async_db),
    uid: str = Depends(current_user_id),
):
    try:
        updated, log = await patch_product(db, product_id, product_in, uid)
        if not updated:
            logger.warning("[patch_product_endpoint] Producto %s no encontrado.", product_id)
            raise HTTPException(status_code=404, detail="Producto no encontrado")
        if log:
            db.add(log)
        await db.commit()
        await db.refresh(updated)
        logger.info("[patch_product_endpoint] Producto %s actualizado parcialmente.", product_id)
        return ProductRead.model_validate(updated)
    except IntegrityError as e:
        await db.rollback()
        logger.error("Integridad en PATCH producto: %s", e, exc_info=True)
        raise HTTPException(status_code=400, detail="Error de integridad de datos.")
    except HTTPException as e:
        await db.rollback()
        raise e
    except Exception as e:
        await db.rollback()
        logger.exception("Error inesperado en PATCH producto", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


# ==============================
# IMPORT MASSIVE PRODUCTS (CSV)
# ==============================
@router.post("/import", status_code=201)
async def import_products(
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

    def _to_decimal(v) -> Decimal:
        try:
            return Decimal(str(v)) if v is not None and str(v).strip() != "" else Decimal("0")
        except (InvalidOperation, ValueError):
            raise HTTPException(status_code=400, detail=f"Valor monetario inválido: {v}")

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

        products = []
        count = 0
        for row in csv_reader:
            count += 1
            try:
                product = Product(
                    code=row["code"],
                    name=row["name"],
                    description=row.get("description") or None,
                    product_type=row["product_type"],
                    category_id=_to_uuid(row.get("category_id")),
                    brand_id=_to_uuid(row.get("brand_id")),
                    unit_id=_to_uuid(row.get("unit_id")),
                    user_id=uid,
                    cost=_to_decimal(row.get("cost")),
                    price=_to_decimal(row.get("price")),
                    percent_tax=float(row.get("percent_tax") or 0),
                    barcode=(row.get("barcode") or None),
                    image_url=(row.get("image_url") or None),
                    negative_stock=_to_bool(row.get("negative_stock")) if row.get("negative_stock") is not None else False,
                    active=_to_bool(row.get("active")) if row.get("active") is not None else True,
                )
                products.append(product)
            except KeyError as ke:
                logger.warning("Fila %d: falta columna requerida: %s", count, ke, exc_info=True)
                raise HTTPException(status_code=400, detail=f"Falta columna requerida: {ke}")
            except HTTPException:
                raise
            except Exception as row_err:
                logger.warning("Fila %d con error: %s", count, row_err, exc_info=True)
                raise HTTPException(status_code=400, detail=f"Error en fila {count}: {row_err}")

        if not products:
            raise HTTPException(status_code=400, detail="No se encontraron filas válidas para importar.")

        db.add_all(products)

        audit_level = await get_audit_level(db)
        if audit_level > 1:
            await log_action(
                db,
                action="IMPORT",
                entity="Product",
                description=f"Importación masiva: {len(products)} productos importados.",
                user_id=uid,
            )

        await db.commit()
        logger.info("Importación masiva de productos exitosa. Total: %d", len(products))
        return {"ok": True, "imported": len(products)}

    except IntegrityError as e:
        await db.rollback()
        logger.error("Integridad en importación de productos: %s", e, exc_info=True)
        raise HTTPException(
            status_code=400,
            detail=f"Error de integridad (producto duplicado u otra restricción): {str(e.orig)}"
        )
    except HTTPException as e:
        await db.rollback()
        logger.error("HTTPException en importación de productos: %s", e.detail, exc_info=True)
        raise e
    except Exception as e:
        await db.rollback()
        logger.exception("Error inesperado en importación de productos", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")