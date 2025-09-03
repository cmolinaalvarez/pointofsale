from __future__ import annotations
from uuid import UUID
from typing import Optional, Tuple, Type
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text
from app.models.document import Document
from fastapi import HTTPException

# ✅ Asegúrate de tener una versión asíncrona de get_setting
# (puedes renombrarla como prefieras)
from app.core.settings import get_setting_async  # <-- implementa/usa tu versión async

async def get_next_document_number_async(
    db: AsyncSession,
    *,
    model,                 # Entry
    document_id: UUID,
    document_date: datetime,
    sequence_field: str = "sequence_number",
    prefix: str = "",
    date_field: str = "created_at",
) -> tuple[str, int]:
    year = document_date.year

    # 1) Lock del tipo de documento para serializar
    dt_locked = await db.execute(
        select(Document).where(Document.id == document_id).with_for_update()
    )
    if dt_locked.scalar_one_or_none() is None:
        raise HTTPException(status_code=404, detail="Tipo de documento no encontrado para numeración.")

    # 2) Máximo consecutivo del año para ese tipo
    date_col = getattr(model, date_field)
    res = await db.execute(
        select(func.coalesce(func.max(getattr(model, sequence_field)), 0)).where(
            model.document_id == document_id,
            func.date_part("year", date_col) == year,
        )
    )
    current_max = int(res.scalar_one() or 0)
    next_seq = current_max + 1

    # 3) Formato del número
    doc_number = f"{prefix}-{year}-{next_seq:05d}" if prefix else f"{year}-{next_seq:05d}"
    return doc_number, next_seq