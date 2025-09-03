
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.setting import Setting

async def get_audit_level(db: AsyncSession) -> int:
    """
    Obtiene el nivel de auditoría configurado globalmente en el sistema.

    Valores posibles:
    - 1: basic   (solo cambios - UPDATE, DELETE, configuración)
    - 2: medium  (cambios y creación - UPDATE, DELETE, CREATE)
    - 3: full    (todas las operaciones CRUD, incluye lecturas/consultas)

    Returns:
        int: Nivel de auditoría actual. Por defecto: 1 (basic)
    """
    result = await db.execute(
        select(Setting.value).where(
            Setting.key == "audit_level",
            Setting.active == True
        )
    )
    value = result.scalar_one_or_none()
    try:
        return int(value)
    except (TypeError, ValueError):
        return 1  # Si no está definido, o el valor no es convertible, default a basic
