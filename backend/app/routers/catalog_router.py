# app/routers/catalog_router.py
from fastapi import APIRouter, Depends, status, Query, UploadFile, File, Body, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, Type
from uuid import UUID

from app.core.security import get_async_db
from app.dependencies.current_user import get_current_user
from app.models.user import User
from app.security.input_validation import validate_upload
from app.core.config import settings

def build_catalog_router(
    *,
    prefix: str,
    tags: list[str],
    crud,
    SCreate: Type,
    SUpdate: Type,
    SRead: Type,
    SPatch: Type,
    SListResponse: Type,
    SImportResult: Optional[Type] = None,
) -> APIRouter:
    router = APIRouter(prefix=prefix, tags=tags)

    @router.post("/", response_model=SRead, status_code=status.HTTP_201_CREATED)
    async def create_item(
        payload: dict = Body(...),
        db: AsyncSession = Depends(get_async_db),
        current_user: User = Depends(get_current_user),
    ):
        data = SCreate.model_validate(payload).model_dump(exclude_none=True)
        obj = await crud.create(db, data, current_user.id)
        await db.commit()
        return obj

    @router.get("/", response_model=SListResponse)
    async def list_items(
        skip: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=1000),
        search: Optional[str] = Query(None),
        active: Optional[bool] = Query(None),
        db: AsyncSession = Depends(get_async_db),
        current_user: User = Depends(get_current_user),
    ):
        data = await crud.list(db, skip, limit, search, active, current_user.id)
        await db.commit()
        return data

    @router.get("/{item_id}", response_model=SRead)
    async def read_item(
        item_id: UUID,
        db: AsyncSession = Depends(get_async_db),
        current_user: User = Depends(get_current_user),
    ):
        obj = await crud.get_by_id(db, item_id)
        await db.commit()
        return obj

    @router.put("/{item_id}", response_model=SRead)
    async def update_item(
        item_id: UUID,
        payload: dict = Body(...),
        db: AsyncSession = Depends(get_async_db),
        current_user: User = Depends(get_current_user),
    ):
        data = SUpdate.model_validate(payload).model_dump(exclude_none=True)
        obj = await crud.update(db, item_id, data, current_user.id)
        await db.commit()
        return obj

    @router.patch("/{item_id}", response_model=SRead)
    async def patch_item(
        item_id: UUID,
        payload: dict = Body(...),
        db: AsyncSession = Depends(get_async_db),
        current_user: User = Depends(get_current_user),
    ):
        data = SPatch.model_validate(payload).model_dump(exclude_unset=True, exclude_none=True)
        obj = await crud.patch(db, item_id, data, current_user.id)
        await db.commit()
        return obj

    @router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
    async def delete_item(
        item_id: UUID,
        db: AsyncSession = Depends(get_async_db),
        current_user: User = Depends(get_current_user),
    ):
        await crud.delete(db, item_id, current_user.id)
        await db.commit()
        return None

    if SImportResult is not None:
        @router.post("/import", response_model=SImportResult, status_code=status.HTTP_201_CREATED)
        async def import_items(
            file: UploadFile = File(...),
            db: AsyncSession = Depends(get_async_db),
            current_user: User = Depends(get_current_user),
        ):
            raw_bytes = validate_upload(file)
            text = raw_bytes.decode("utf-8", errors="ignore")
            lines = [ln for ln in text.splitlines() if ln.strip()]
            if len(lines) > 1 and (len(lines) - 1) > settings.MAX_IMPORT_ROWS:
                raise HTTPException(status_code=400, detail="Demasiadas filas en el archivo")
            result = await crud.import_csv_text(db, text, current_user.id)
            await db.commit()
            return result

    return router
