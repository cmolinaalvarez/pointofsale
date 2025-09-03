from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel

class AuditLogCreate(BaseModel):
    action: str  # Acción: CREATE, UPDATE, DELETE, etc.
    entity: str  # Entidad afectada: Brand, User, etc.
    entity_id: Optional[UUID] = None  # ID de la entidad (si aplica)
    description: str  # Descripción detallada del evento
    user_id: UUID  # Usuario que ejecutó la acción

    # El backend decide si guarda updated_at manualmente
    updated_at: Optional[datetime] = None
