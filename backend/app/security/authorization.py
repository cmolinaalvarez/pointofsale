from __future__ import annotations
from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.user import User
from app.models.role import RoleTypeEnum, Role
from app.core.security import get_async_db
from app.security.authentication import get_current_user

def _deny(): raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

def has_permission(user: User, scope: str) -> bool:
    if user.superuser: return True
    if not user.role:  return False
    scopes = user.role.scopes or []
    return scope in scopes

def requires_role(*accepted: RoleTypeEnum):
    async def _dep(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_async_db)):
        if user.superuser: return
        if not user.role_id: _deny()
        role_type = (await db.execute(select(Role.role_type).where(Role.id==user.role_id))).scalar_one_or_none()
        if role_type not in accepted: _deny()
    return _dep

def requires_scopes(*required_scopes: str):
    async def _dep(user: User = Depends(get_current_user)):
        if user.superuser: return
        for s in required_scopes:
            if not has_permission(user, s): _deny()
    return _dep
