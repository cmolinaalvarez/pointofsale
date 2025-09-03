# app/crud/audit_log.py
from app.models.audit_log import AuditLog
from app.schemas.audit_log import AuditLogCreate
from sqlalchemy.ext.asyncio import AsyncSession

async def create_audit_log(
    db: AsyncSession,
    log_in: AuditLogCreate
) -> AuditLog:
    """
    Agrega un log de auditoría a la sesión. No hace commit.
    """
    audit_log = AuditLog(**log_in.model_dump())
    db.add(audit_log)
    return audit_log  # Retornamos el objeto por si se quiere usar luego
