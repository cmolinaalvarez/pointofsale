"""
API Router for Role management (Simplified)
"""

from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status, UploadFile, File
import csv
from io import StringIO
import logging
from sqlalchemy import select, func
from app.utils.audit import log_action
from app.utils.audit_level import get_audit_level
from app.models.role import Role, RoleType
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security import get_async_db
from app.dependencies.current_user import get_current_user
# from app.core.oauth2_middleware import require_scope  # Comentado temporalmente
from app.models.user import User  # Usar el modelo User correcto
from app.crud.role import role_crud
from app.schemas.role import (
    RoleCreate, RoleUpdate, RolePatch, RoleRead, RoleListResponse
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Roles"])


# ======================
# ENDPOINTS DE ROLES - CRUD BÁSICO
# ======================

@router.get("/", response_model=RoleListResponse)
# @require_scope("read")  # Comentado temporalmente
async def get_roles(
    skip: int = Query(0, ge=0, description="Número de registros a omitir"),
    limit: int = Query(100, ge=1, le=1000, description="Límite de registros"),
    role_type: Optional[RoleType] = Query(None, description="Filtrar por tipo de rol"),
    active: Optional[bool] = Query(None, description="Filtrar por estado activo"),
    search: Optional[str] = Query(None, description="Búsqueda en código, nombre o descripción"),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """
    Obtener lista de roles con filtros opcionales
    """
    try:
        roles, total = await role_crud.get_multi(
            db=db,
            skip=skip,
            limit=limit,
            role_type=role_type,
            active=active,
            search=search
        )
        
        return RoleListResponse(total=total, items=roles)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener roles: {str(e)}"
        )


@router.get("/{role_id}", response_model=RoleRead)
# @require_scope("read")  # Comentado temporalmente
async def get_role(
    role_id: UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """
    Obtener un rol específico por ID
    """
    role = await role_crud.get(db, role_id)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rol no encontrado"
        )
    return role


@router.post("/", response_model=RoleRead, status_code=status.HTTP_201_CREATED)
# @require_scope("write")  # Comentado temporalmente
async def create_role(
    role_in: RoleCreate,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """Crear un nuevo rol"""
    try:
        role = await role_crud.create(db, role_in, current_user.id)
        return role
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al crear rol: {str(e)}"
        )


@router.put("/{role_id}", response_model=RoleRead)
# @require_scope("write")  # Comentado temporalmente
async def update_role(
    role_id: UUID,
    role_in: RoleUpdate,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """Actualizar un rol existente"""
    try:
        updated_role, log = await role_crud.update(db, role_id, role_in, current_user.id)
        if not updated_role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Rol no encontrado"
            )
        return updated_role
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al actualizar rol: {str(e)}"
        )


@router.patch("/{role_id}", response_model=RoleRead)
# @require_scope("write")  # Comentado temporalmente
async def patch_role(
    role_id: UUID,
    role_in: RolePatch,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """
    Actualización parcial de un rol
    """
    try:
        updated_role, log = await role_crud.patch(db, role_id, role_in, current_user.id)
        if not updated_role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Rol no encontrado"
            )
        return updated_role
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al actualizar rol: {str(e)}"
        )
        
        
        
# ==============================
# IMPORT MASSIVE ROLES (consolidado)
# ==============================
@router.post("/import", status_code=201)
async def import_roles(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    def as_bool(v, default=False):
        return str(v).strip().lower() in {"true","1","yes","si","y","t"} if v is not None else default

    def parse_role_type(raw: Optional[str]) -> RoleType:
        if not raw:
            return RoleType.VIEWER
        val = raw.strip().lower()
        for rt in RoleType:
            if rt.value == val:
                return rt
        return RoleType.VIEWER

    def parse_scopes(raw: Optional[str]) -> Optional[list]:
        if not raw:
            return None
        parts = [p.strip() for p in raw.replace(";", ",").split(",") if p.strip()]
        return parts or None

    try:
        raw = await file.read()
        for enc in ("utf-8-sig", "utf-8", "latin-1"):
            try:
                text = raw.decode(enc)
                break
            except UnicodeDecodeError:
                continue

        reader = csv.DictReader(StringIO(text))
        if reader.fieldnames:
            reader.fieldnames = [h.strip().replace("\ufeff", "") for h in reader.fieldnames]
            logger.info(f"Headers después de limpieza: {reader.fieldnames}")

        # Nombres ya existentes en BD (lowercase)
        res = await db.execute(select(func.lower(Role.name)))
        existing_names = set(res.scalars().all())

        roles: list[Role] = []
        seen_in_file: set[str] = set()
        skipped_dups = 0

        with db.no_autoflush:
            for i, row in enumerate(reader, start=1):
                name = (row.get("name") or "").strip()
                if not name:
                    continue

                key = name.lower()  # <-- si tu unicidad es (name, role_type), usa: key = (name.lower(), parse_role_type(row.get("role_type")).value)
                if key in seen_in_file or key in existing_names:
                    skipped_dups += 1
                    continue

                role = Role(
                    name=name,
                    description=((row.get("description") or "").strip() or None),
                    role_type=parse_role_type(row.get("role_type")),
                    scopes=parse_scopes(row.get("scopes")),
                    is_admin=as_bool(row.get("is_admin"), False),
                    active=as_bool(row.get("active"), True),
                    user_id=current_user.id,
                )
                roles.append(role)
                seen_in_file.add(key)

        if not roles:
            raise HTTPException(status_code=400, detail="No se encontraron filas válidas para importar.")

        db.add_all(roles)

        audit_level = await get_audit_level(db)
        if audit_level > 1:
            await log_action(
                db, action="IMPORT", entity="Role",
                description=f"Importación masiva: {len(roles)} roles importados (omitidos por duplicado: {skipped_dups}).",
                user_id=current_user.id
            )

        try:
            await db.commit()
        except IntegrityError as e:
            await db.rollback()
            raise HTTPException(
                status_code=400,
                detail=f"Error de integridad (posible rol duplicado): {str(e.orig)}"
            )

        return {"ok": True, "imported": len(roles), "skipped_duplicates": skipped_dups}

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.exception("Error inesperado importando roles")
        raise HTTPException(status_code=500, detail=f"Error interno: {e}")