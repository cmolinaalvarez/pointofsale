# app/utils/audit.py
from app.models.audit_log import AuditLog
from sqlalchemy.ext.asyncio import AsyncSession

async def log_action(
    db: AsyncSession,
    *,
    action: str,
    entity: str,
    description: str,
    user_id,
    entity_id=None,
    updated_at=None
):
    log_data = {
        "action": action,
        "entity": entity,
        "entity_id": entity_id,
        "description": description,
        "user_id": user_id
    }
    # Solo incluye updated_at si se especifica
    if updated_at is not None:
        log_data["updated_at"] = updated_at

    log = AuditLog(**log_data)
    db.add(log)
    await db.flush()
    return log