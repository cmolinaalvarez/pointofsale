from pydantic import BaseModel
from uuid import UUID
from typing import Optional, List
from datetime import datetime

# ============================================================
# BASE (Campos compartidos)
# ============================================================
class UnitBase(BaseModel):
    name: str
    description: Optional[str] = None
    symbol: str
    active: bool = True

# ============================================================
# CREAR (POST)
# ============================================================
class UnitCreate(UnitBase):
    pass

# ============================================================
# ACTUALIZAR COMPLETO (PUT)
# ============================================================
class UnitUpdate(UnitBase):
    pass

# ============================================================
# ACTUALIZAR PARCIAL (PATCH)
# ============================================================
class UnitPatch(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    symbol: Optional[str] = None
    active: Optional[bool] = None
    user_id: Optional[UUID] = None

# ============================================================
# RESPUESTA DE LECTURA (GET)
# ============================================================
class UnitRead(UnitBase):
    id: UUID
    name: Optional[str] = None
    description: Optional[str] = None
    symbol: Optional[str] = None
    active: Optional[bool] = None
    user_id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# ============================================================
# RESPUESTA PAGINADA
# ============================================================
class UnitListResponse(BaseModel):
    total: int
    items: List[UnitRead]

    class Config:
        from_attributes = True

# ============================================================
# RESULTADO DE IMPORTACIÓN MASIVA
# ============================================================
class UnitImportResult(BaseModel):
    total_imported: int
    total_errors: int
    imported: list
    errors: list
