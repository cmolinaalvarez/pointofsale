"""Router de Usuario con actor_id para auditoría."""

from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from uuid import UUID
from typing import Optional
import logging
import csv
from io import StringIO
import bcrypt

from app.schemas.user import UserCreate, UserUpdate, UserRead, UserPatch, UserListResponse
from app.crud.user import create_user, get_users, get_user_by_id, update_user, patch_user
from app.models.user import User
from app.dependencies.current_user import get_current_user
from app.core.security import get_async_db
from app.utils.audit import log_action

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Users"])


@router.post("/", response_model=UserRead)
async def create_user_endpoint(
    user_in: UserCreate,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    try:
        user, log = await create_user(db, user_in, current_user.id)
        if log:
            db.add(log)
        await db.commit()
        return UserRead.model_validate(user)
    except IntegrityError as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=f"Integridad: {e.orig}")
    except SQLAlchemyError:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Error BD")
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=UserListResponse)
async def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = None,
    active: Optional[bool] = None,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    try:
        data = await get_users(db, skip, limit, search, active, current_user.id)
        await db.commit()
        return data
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Error listando usuarios") from e


@router.get("/{user_id}", response_model=UserRead)
async def read_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    try:
        user = await get_user_by_id(db, user_id, current_user.id)
        await db.commit()
        return UserRead.model_validate(user)
    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Error obteniendo usuario") from e


@router.put("/{user_id}", response_model=UserRead)
async def update_user_endpoint(
    user_id: UUID,
    user_in: UserUpdate,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    try:
        updated, log = await update_user(db, user_in, user_id, current_user.id)
        if not updated:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        if log:
            db.add(log)
        await db.commit()
        await db.refresh(updated)
        return UserRead.model_validate(updated)
    except HTTPException:
        await db.rollback()
        raise
    except IntegrityError as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=f"Integridad: {e.orig}")
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{user_id}", response_model=UserRead)
async def patch_user_endpoint(
    user_id: UUID,
    user_in: UserPatch,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    try:
        updated, log = await patch_user(db, user_in, user_id, current_user.id)
        if not updated:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        if log:
            db.add(log)
        await db.commit()
        await db.refresh(updated)
        return UserRead.model_validate(updated)
    except HTTPException:
        await db.rollback()
        raise
    except IntegrityError as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=f"Integridad: {e.orig}")
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/import", status_code=201)
async def import_users(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user),
):
    try:
        content = await file.read()
        reader = csv.DictReader(StringIO(content.decode("utf-8")))
        if reader.fieldnames:
            reader.fieldnames = [h.strip().replace('\ufeff', '') for h in reader.fieldnames]
        to_add = []
        for row in reader:
            pwd = row.get("password")
            if not pwd:
                continue
            hashed = bcrypt.hashpw(pwd.encode(), bcrypt.gensalt()).decode()
            user = User(
                username=row.get("username"),
                email=row.get("email"),
                full_name=row.get("full_name"),
                password=hashed,
                active=str(row.get("active", "true")).lower() in ("true", "1", "yes", "si"),
                superuser=str(row.get("superuser", "false")).lower() in ("true", "1", "yes", "si"),
                user_id=current_user.id,
            )
            to_add.append(user)
        if not to_add:
            raise HTTPException(status_code=400, detail="Archivo sin filas válidas")
        db.add_all(to_add)
        await log_action(
            db,
            action="IMPORT",
            entity="User",
            description=f"Importó {len(to_add)} usuarios",
            user_id=current_user.id,
        )
        await db.commit()
        return {"imported": len(to_add)}
    except HTTPException:
        await db.rollback()
        raise
    except IntegrityError as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=f"Integridad: {e.orig}")
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
