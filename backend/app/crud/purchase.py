# app/crud/purchase.py
# ==========================================================================================
# CRUD de "Purchase" (compras de inventario) totalmente asíncrono.
# - Genera numeración consecutiva por tipo de documento/año.
# - Inserta cabecera (Purchase) e ítems (PurchaseItem).
# - Ajusta stock por bodega/producto usando un helper externo (sin commits internos).
# - Registra auditoría condicional según nivel configurado.
# - Maneja la transacción de manera manual (commit/rollback) SIN usar `with db.begin()`.
# - Evita "MissingGreenlet" precargando relaciones con `selectinload` antes de serializar.
# ==========================================================================================

from __future__ import annotations
# ↑ Permite usar anotaciones de tipos como strings "adelantadas" (forward references)
#   sin necesidad de importar/definir las clases antes (útil cuando hay dependencias cíclicas
#   entre schemas/modelos o cuando los tipos aún no están definidos en tiempo de parseo).

from datetime import datetime
# ↑ Marca temporal consistente (UTC recomendado) para numeración, timestamps y auditoría.

from uuid import UUID
# ↑ Tipo para IDs universales. Útil cuando el modelo usa UUID como PK o FK (consistencia de tipos).

from decimal import Decimal
# ↑ Precisión exacta (evita errores binarios de float) para montos, cantidades y totales.

from typing import Optional, Tuple
# ↑ Tipado estático (opcional) para mayor claridad:
#   - Optional[T] indica que un valor puede ser T o None.
#   - Tuple[...] te sirve si alguna función retorna tuplas (p.ej., (purchase, audit_log)).

import logging
# ↑ Logging estructurado (nivel módulo). Útil para trazabilidad, debugging y auditoría técnica.

# ──────────────────────────────────────────────────────────────────────────────
# SQLAlchemy (modo asíncrono)
# ──────────────────────────────────────────────────────────────────────────────
from sqlalchemy.ext.asyncio import AsyncSession
# ↑ Sesión asíncrona. TODAS las operaciones de BD aquí deben ser awaitables.

from sqlalchemy.exc import IntegrityError, SQLAlchemyError
# ↑ Excepciones de SQLAlchemy:
#   - IntegrityError: violaciones de unicidad, FK, NOT NULL, etc.
#   - SQLAlchemyError: catch-all para errores del ORM/engine.

from sqlalchemy import select
# ↑ Constructor de SELECTs en modo 2.0 (declarativo), ideal para async.

from sqlalchemy.orm import selectinload
# ↑ Estrategia de carga ansiosa (eager) que hace "IN (...)": evita lazy-loading en async
#   (previene MissingGreenlet) y reduce N+1 queries al precargar relaciones necesarias.

# ──────────────────────────────────────────────────────────────────────────────
# FastAPI
# ──────────────────────────────────────────────────────────────────────────────
from fastapi import HTTPException
# ↑ Para mapear errores de dominio/infraestructura a respuestas HTTP (4xx/5xx).

# ──────────────────────────────────────────────────────────────────────────────
# Modelos de BD (capa de persistencia)
# ──────────────────────────────────────────────────────────────────────────────
from app.models.purchase import Purchase, PurchaseItem
# ↑ Entidades principales:
#   - Purchase: cabecera del documento de compra.
#   - PurchaseItem: renglones de productos/cantidades por compra.

from app.models.audit_log import AuditLog
# ↑ Entidad de auditoría (si tu helper de auditoría devuelve/usa el modelo directamente).

# ──────────────────────────────────────────────────────────────────────────────
# Schemas (Pydantic) — capa de validación/IO
# ──────────────────────────────────────────────────────────────────────────────
from app.schemas.purchase import PurchaseCreate
# ↑ Esquemas de compra:
#   - PurchaseCreate: payload para crear una compra y sus ítems.
#   - PurchasePatch: payload para modificaciones parciales (aunque en este archivo no se use,
#                 suele convivir para mantener cohesión del módulo).

# ──────────────────────────────────────────────────────────────────────────────
# Núcleo de negocio: numeración y metadatos de documento
# ──────────────────────────────────────────────────────────────────────────────
from app.core.sequence import get_next_document_number_async
# ↑ Genera número consecutivo considerando tipo de documento y año (thread-safe en BD).

from app.crud.document import get_document_by_id
# ↑ Recupera el tipo de documento (prefijo, reglas) para validar y construir el número final.

# ──────────────────────────────────────────────────────────────────────────────
# Auditoría y utilidades
# ──────────────────────────────────────────────────────────────────────────────
from app.utils.audit import log_action
# ↑ Inserta un registro de auditoría (acción, entidad, id, descripción, usuario).

from app.utils.audit_level import get_audit_level
# ↑ Lee el nivel de auditoría desde settings (1=basic, 2=medium, 3=full) para decidir qué loguear.

from app.helper.stock import adjust_stock_quantity
# ↑ Helper transaccional que ajusta stock con SELECT ... FOR UPDATE (sin commit), seguro en concurrencia.

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
import logging

# ──────────────────────────────────────────────────────────────────────────────
# Logger del módulo
# ──────────────────────────────────────────────────────────────────────────────
logger = logging.getLogger(__name__)
# ↑ Usa el nombre del módulo como categoría. Configura handlers/formatters a nivel app.
#   Ejemplos de uso:
#     logger.info("Creando Purchase %s", purchase_id)
#     logger.warning("Stock insuficiente para product_id=%s", product_id)
#     logger.exception("Fallo al crear compra")  # incluye traceback

async def create_purchase(
    db: AsyncSession,
    purchase_in: PurchaseCreate,
    user_id: Optional[UUID] = None,
    audit_document: bool = False,
) -> Purchase:
    """
    Crea una compra (Purchase) con sus ítems (PurchaseItem), ajusta el stock por bodega/producto
    usando `adjust_stock_quantity` y registra auditoría dependiendo del nivel configurado.

    ⚙️ Flujo:
      1) Calcula fecha base y obtiene el tipo de documento (prefijo).
      2) Genera numeración consecutiva segura (posible uso de locks/advisory en la impl. interna).
      3) Inserta cabecera e ítems.
      4) Ajusta stock acumulando delta POSITIVO (compras aumentan inventario).
      5) Registra auditoría si corresponde.
      6) Commit explícito al final. Si algo falla, rollback.

    🔒 Transacción:
      - No se utiliza `with db.begin()` por petición expresa.
      - `adjust_stock_quantity` NO debe hacer `commit()` ni `rollback()`.
      - Cualquier excepción dispara `await db.rollback()` y se re-lanza traducida a HTTPException.

    Args:
        db: AsyncSession activo para la transacción.
        purchase_in: Payload validado de Pydantic con cabecera e ítems.
        user_id: Usuario que ejecuta la operación (para auditoría).
        audit_document_type: Si tu capa de `document_type` soporta auditar lecturas, pásalo en True.

    Returns:
        Purchase: La compra recién creada, con sus `items` precargados (selectinload) lista para serializar.

    Raises:
        HTTPException: 4xx/5xx según el tipo de error y el punto de fallo.
    """
    try:
        # ----------------------------------------------------------------------------------
        # 1) FECHA BASE PARA NUMERACIÓN
        # ----------------------------------------------------------------------------------
        # Si el cliente envió una fecha (útil para backdating), úsala; de lo contrario, ahora (UTC).
        doc_date = getattr(purchase_in, "date", None) or datetime.utcnow()
        print("DOC_DATE ::::::::::::::::::::::",doc_date)
        # ----------------------------------------------------------------------------------
        # 2) TIPO DE DOCUMENTO Y PREFIJO
        # ----------------------------------------------------------------------------------
        # Consultamos el tipo de documento para obtener el prefijo. Si no existe, abortamos.
        # Nota: Si implementaste auditoría de lecturas de catálogos, `audit_document_type`
        # puede ayudar a registrar esta operación (depende de `get_document_type_by_id`).
        doc_type = await get_document_by_id(db, purchase_in.document_id, user_id, audit_document)
        print("DOC_TYPE ::::::::::::::::::::::",doc_type)
        if not doc_type:
            # Importante: mapeamos a 404 porque el tipo de documento es requerido y no existe.
            raise HTTPException(status_code=404, detail="Tipo de documento no encontrado.")
        prefix = doc_type.prefix or ""  # Si no hay prefijo, usamos cadena vacía y seguimos.

        # ----------------------------------------------------------------------------------
        # 3) GENERAR NUMERACIÓN CORRELATIVA
        # ----------------------------------------------------------------------------------
        # `get_next_document_number_async` debe ser segura ante concurrentes:
        # - Puede usar advisory locks por (tipo_documento, año) o similar.
        # - Devuelve el número legible y la secuencia interna para la cabecera.
        # - Filtra por año usando `date_field` (aquí 'created_at') si así lo definiste en la impl.
        doc_number, sequence = await get_next_document_number_async(
            db=db,
            model=Purchase,                                # Modelo sobre el que se calcula la secuencia
            document_id=purchase_in.document_id,           # Si la secuencia depende del tipo, úsalo
            document_date=doc_date,                     # Año base para reinicio (si aplica)
            sequence_field="sequence_number",           # Campo entero incremental interno
            prefix=prefix,                              # Prefijo del tipo de documento (opcional)
            date_field="created_at",                    # Campo de fecha en la tabla para filtrar por año
        )

        # ----------------------------------------------------------------------------------
        # 4) PREPARAR DATOS DE CABECERA (ENTRY)
        # ----------------------------------------------------------------------------------
        # `model_dump(exclude_unset=True)` evita que campos no enviados (por default) sobreescriban valores.
        purchase_data = purchase_in.model_dump(exclude_unset=True)

        # Extraemos items del payload para insertarlos en su propia tabla
        items_data = purchase_data.pop("items", [])
        # Inject numeración generada en la cabecera
        purchase_data["purchase_number"] = doc_number
        purchase_data["sequence_number"] = sequence

        # ----------------------------------------------------------------------------------
        # 5) INSERTAR CABECERA
        # ----------------------------------------------------------------------------------
        # Creamos la cabecera y hacemos `flush()` para conseguir el `purchase.id` sin cerrar la transacción.
        purchase = Purchase(**purchase_data)
        db.add(purchase)
        await db.flush()  # => purchase.id disponible para FK en items y logs

        # ----------------------------------------------------------------------------------
        # 6) INSERTAR ÍTEMS Y AJUSTAR STOCK
        # ----------------------------------------------------------------------------------
        # Validación mínima: al menos un ítem por compra
        if not items_data:
            raise HTTPException(status_code=400, detail="Debe enviar al menos un ítem.")

        # Por cada ítem:
        #  - Insertar en `purchase_items`
        #  - Ajustar el stock de (warehouse_id, product_id) con delta POSITIVO
        #    (porque esta operación es una ENTRADA de inventario).
        for item_dict in items_data:
            # 6.1) Insertar ítem
            db_item = PurchaseItem(
                purchase_id=purchase.id,
                product_id=item_dict["product_id"],
                quantity=item_dict["quantity"],
                subtotal=item_dict["subtotal"],
                discount=item_dict["discount"],
                tax=item_dict["tax"],
                total=item_dict["total"],
            )
            db.add(db_item)

           
        # ----------------------------------------------------------------------------------
        # 7) AUDITORÍA DE LA CREACIÓN DE ENTRADA (CONDICIONAL)
        # ----------------------------------------------------------------------------------
        # Solo registramos si el nivel de auditoría lo amerita y tenemos `user_id` del operador.
        audit_level = await get_audit_level(db)
        if audit_level > 1 and user_id:
            db.add(
                AuditLog(
                    user_id=user_id,                 # Importante: el usuario autenticado que ejecuta la acción
                    action="CREATE",
                    entity="Purchase",
                    entity_id=purchase.id,
                    description=f"Entrada creada con número {doc_number}",
                )
            )
        # Nota: no hacemos `flush()` extra aquí; con el `commit()` de más abajo es suficiente.

        # ----------------------------------------------------------------------------------
        # 8) COMMIT FINAL
        # ----------------------------------------------------------------------------------
        # Si todo salió bien (cabecera, ítems, stock, auditoría), confirmamos.
        await db.commit()

        # ----------------------------------------------------------------------------------
        # 9) RECARGA CON RELACIONES PRE-CARGADAS (EAGER) PARA SERIALIZAR
        # ----------------------------------------------------------------------------------
        # En async, acceder a relaciones lazy fuera de un contexto de greenlet puede disparar
        # `MissingGreenlet`. Para devolver el objeto completo ya serializable, recargamos
        # la entidad con `selectinload(Purchase.items)`.
        res = await db.execute(
            select(Purchase)
            .options(selectinload(Purchase.items))
            .where(Purchase.id == purchase.id)
        )
        # `scalar_one()` falla si no hay exactamente una fila; si lo prefieres tolerante, usa `scalar_one_or_none()`.
        return res.scalar_one()

    # ======================================================================================
    # MANEJO DE ERRORES: SIEMPRE HACER ROLLBACK CUANDO HAYA FALLOS ANTES DEL COMMIT
    # ======================================================================================
    except IntegrityError as ie:
        # Ej.: Restricciones únicas, FK obligatorias, etc.
        await db.rollback()
        # Propagamos error claro al cliente (400 Bad Request) con causa subyacente
        raise HTTPException(status_code=400, detail=f"Error de integridad creando Purchase: {ie.orig}") from ie

    except HTTPException:
        # Para errores controlados (validador, no encontrado, etc.) solo hacemos rollback y re-lanzamos
        await db.rollback()
        raise

    except Exception as e:
        # Cualquier otro error inesperado (programación, red, etc.)
        await db.rollback()
        # Logueamos para diagnóstico (stacktrace) y mapeamos a 500 genérico
        logger.exception("Error inesperado en create_purchase", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error interno al crear la compra: {e}")


# -------------------------------
# READ: GET BY ID (con auditoría condicional)
# -------------------------------
async def get_purchase(
    db: AsyncSession,
    purchase_id: UUID,
    user_id: Optional[UUID] = None,  # para auditar lecturas si nivel > 2
) -> Purchase | None:
    try:
        res = await db.execute(
            select(Purchase)
            .options(selectinload(Purchase.items))
            .where(Purchase.id == purchase_id)
        )
        purchase = res.scalar_one_or_none()
        if not purchase:
            return None

        # Auditoría de lectura si el nivel lo pide
        audit_level = await get_audit_level(db)
        if audit_level > 2 and user_id:
            await log_action(
                db,
                action="GETID",
                entity="Purchase",
                entity_id=purchase.id,
                description=f"Consultó compra: {purchase.purchase_number}",
                user_id=user_id,
            )
            await db.flush()  # sin commit en GET

        return purchase

    except SQLAlchemyError as e:
        await db.rollback()
        logger.error("[get_purchase] Error SQLAlchemy: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Error al consultar la compra")
    except Exception as e:
        await db.rollback()
        logger.exception("[get_purchase] Error inesperado", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


# -------------------------------
# READ: GET LIST (mantiene retorno list[Purchase])
# -------------------------------
async def get_purchases(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 10,
    user_id: Optional[UUID] = None,  # para auditar lecturas si nivel > 2
) -> list[Purchase]:
    try:
        res = await db.execute(
            select(Purchase)
            .options(selectinload(Purchase.items))
            .order_by(Purchase.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        purchases = list(res.scalars().all())

        # Auditoría de lectura masiva
        audit_level = await get_audit_level(db)
        if audit_level > 2 and user_id:
            await log_action(
                db,
                action="GETALL",
                entity="Purchase",
                description=f"Consulta de Compras - skip={skip}, limit={limit}",
                user_id=user_id,
            )
            await db.flush()  # sin commit en GET

        return purchases

    except SQLAlchemyError as e:
        await db.rollback()
        logger.error("[get_purchases] Error SQLAlchemy: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Error al listar compras")
    except Exception as e:
        await db.rollback()
        logger.exception("[get_purchases] Error inesperado", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")
    
    
async def deactivate_purchase_and_return_stock(
    db: AsyncSession,
    purchase_id: UUID,
    user_id: Optional[UUID] = None,
) -> Tuple[Optional[Purchase], Optional[dict]]:
    """
    Inactiva la compra y recalcula el stock por producto en su bodega:
    stock(producto, bodega) = sum(Compras activas) - sum(Salidas activas)
    """
    try:
        # 1) Cargar la compra con ítems
        res = await db.execute(
            select(Purchase)
            .where(Purchase.id == purchase_id)
            .options(selectinload(Purchase.items))
        )
        purchase: Purchase | None = res.scalars().first()

        if not purchase:
            logger.info(f"[deactivate_purchase] Compra {purchase_id} no encontrada.")
            return None, None

        # 2) Idempotencia
        if purchase.active is False:
            logger.info(f"[deactivate_purchase] Compra {purchase_id} ya estaba inactiva. Sin cambios.")
            await db.flush()
            return purchase, None

        # 3) Marcar inactiva
        purchase.active = False
        purchase.updated_at = datetime.utcnow()

        # 4) Recalcular stock por producto (Compras - Salidas)
        #    - Hacemos flush para que esta compra ya NO cuente en los SELECT del recalculo
        await db.flush()

        product_ids = {it.product_id for it in (purchase.items or [])}
       
        # 5) Auditoría
        audit_level = await get_audit_level(db)
        log_dict: Optional[dict] = None
        if audit_level >= 1 and user_id:
            description = (
                "Compra cancelada."
                f"Productos afectados: {len(product_ids)}"
            )
            log = await log_action(
                db=db,
                action="UPDATE",
                entity="Purchase",
                entity_id=purchase.id,
                description=description,
                user_id=user_id,
            )
            log_dict = {
                "id": str(getattr(log, "id", None)),
                "action": "UPDATE",
                "entity": "Purchase",
                "entity_id": str(purchase.id),
                "description": description,
                "created_at": getattr(log, "created_at", None),
            }

        await db.flush()
        logger.info("[deactivate_purchase] Compra %s cancelada por el usuario %s.", purchase_id, user_id)
        return purchase, log_dict

    except IntegrityError as e:
        await db.rollback()
        logger.error("[deactivate_purchase] Error de integridad: %s", e, exc_info=True)
        raise HTTPException(status_code=400, detail="Error de integridad de datos: " + str(getattr(e, "orig", e)))
    except SQLAlchemyError as e:
        await db.rollback()
        logger.error("[deactivate_purchase] Error SQLAlchemy: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Error en la base de datos")
    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        logger.exception("[deactivate_purchase] Error inesperado", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")