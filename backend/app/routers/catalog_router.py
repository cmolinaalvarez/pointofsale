# app/routers/catalog_router.py
from fastapi import APIRouter, Depends, status, Query, UploadFile, File, Body
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, Type
from uuid import UUID

from app.core.security import get_async_db
from app.dependencies.current_user import get_current_user
from app.models.user import User

def build_catalog_router(
    *,
    prefix: str,
    tags: list[str],
    crud,                         # CatalogCRUD
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
        payload: SCreate = Body(...),
        db: AsyncSession = Depends(get_async_db),
        current_user: User = Depends(get_current_user),
    ):
        obj = await crud.create(db, payload.model_dump(), current_user.id)
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
        payload: SUpdate = Body(...),
        db: AsyncSession = Depends(get_async_db),
        current_user: User = Depends(get_current_user),
    ):
        obj = await crud.update(db, item_id, payload.model_dump(), current_user.id)
        await db.commit()
        return obj

    @router.patch("/{item_id}", response_model=SRead)
    async def patch_item(
        item_id: UUID,
        payload: SPatch = Body(...),
        db: AsyncSession = Depends(get_async_db),
        current_user: User = Depends(get_current_user),
    ):
        obj = await crud.patch(db, item_id, payload.model_dump(exclude_unset=True), current_user.id)
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
            text = (await file.read()).decode(errors="ignore")
            result = await crud.import_csv_text(db, text, current_user.id)
            await db.commit()
            return result

    return router
