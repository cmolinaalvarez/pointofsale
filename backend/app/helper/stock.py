# =============================================================================
# IMPORTACIONES
# =============================================================================
from decimal import Decimal
from datetime import datetime

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.stock import Stock
from app.models.entry import Entry, EntryItem
from app.models.document import Document
from app.utils.audit_level import get_audit_level
from app.utils.audit import log_action


# =============================================================================
# FUNCIÓN PRINCIPAL (misma firma)
# =============================================================================
async def adjust_stock_quantity(
    db: AsyncSession,
    *,
    product_id,
    warehouse_id,
    delta: Decimal,          # <-- se conserva por compatibilidad, no se usa
    user_id=None,
    reason: str = "",
) -> Stock:
    """
    Recalcula y establece el stock como:
        stock = SUM(Items.quantity en Entradas activas) - SUM(Items.quantity en Salidas activas)

    - Si no existe (product_id, warehouse_id) en Stock, lo crea con cantidad inicial 0 y luego lo ajusta.
    - Bloquea la fila de Stock con FOR UPDATE para evitar carreras.
    - Si el resultado fuese negativo, levanta ValueError (misma política que antes).
    - Registra auditoría según nivel configurado.
    - No hace commit (sólo flush); el caller controla commit/rollback.
    """

    # 1) Bloqueo/obtención de la fila de stock (o crearla si no existe)
    stmt_lock = (
        select(Stock)
        .where(Stock.product_id == product_id, Stock.warehouse_id == warehouse_id)
        .with_for_update()
    )
    res_stock = await db.execute(stmt_lock)
    stock = res_stock.scalar_one_or_none()

    if stock is None:
        stock = Stock(
            product_id=product_id,
            warehouse_id=warehouse_id,
            quantity=Decimal("0"),
            active=True,
            user_id=user_id,
        )
        db.add(stock)
        await db.flush()

    # 2) Calcular SUM(entradas) y SUM(salidas) sobre documentos ACTIVOS
    #    Document.document_type: 'E' (Entrada), 'S' (Salida)
    sum_in_stmt = (
        select(func.coalesce(func.sum(EntryItem.quantity), 0))
        .select_from(EntryItem)
        .join(Entry, EntryItem.entry_id == Entry.id)
        .join(Document, Entry.document_id == Document.id)
        .where(
            EntryItem.product_id == product_id,
            Entry.warehouse_id == warehouse_id,
            Entry.active.is_(True),
            Document.document_type == "E",
        )
    )
    sum_out_stmt = (
        select(func.coalesce(func.sum(EntryItem.quantity), 0))
        .select_from(EntryItem)
        .join(Entry, EntryItem.entry_id == Entry.id)
        .join(Document, Entry.document_id == Document.id)
        .where(
            EntryItem.product_id == product_id,
            Entry.warehouse_id == warehouse_id,
            Entry.active.is_(True),
            Document.document_type == "S",
        )
    )

    res_in = await db.execute(sum_in_stmt)
    res_out = await db.execute(sum_out_stmt)

    # Asegurar Decimal exacto
    def _to_dec(v) -> Decimal:
        if isinstance(v, Decimal):
            return v
        return Decimal(str(v or "0"))

    total_in = _to_dec(res_in.scalar_one())
    total_out = _to_dec(res_out.scalar_one())

    # 3) Nuevo stock = entradas - salidas (política: no permitir negativo)
    old_qty = _to_dec(stock.quantity or 0)
    new_qty = total_in - total_out
    if new_qty < 0:
        raise ValueError(
            f"Stock resultante negativo para product={product_id} en warehouse={warehouse_id} "
            f"(Entradas={total_in} - Salidas={total_out} = {new_qty})."
        )

    stock.quantity = new_qty
    stock.updated_at = datetime.utcnow()

    # 4) Auditoría (mantiene misma acción/estilo que la versión anterior)
    audit_level = await get_audit_level(db)
    if audit_level >= 1 and user_id:
        desc = (
            f"Stock recalculado {old_qty} → {new_qty} "
            f"(Entradas={total_in} - Salidas={total_out})"
        )
        if reason:
            desc += f" - {reason}"

        await log_action(
            db,
            action="STOCK_ADJUST",
            entity="Stock",
            entity_id=stock.id,
            description=desc,
            user_id=user_id,
        )

    # 5) Persistir en la transacción (sin commit)
    await db.flush()

    return stock
