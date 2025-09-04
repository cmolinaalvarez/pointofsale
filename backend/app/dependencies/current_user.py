from __future__ import annotations
from fastapi import Depends
from app.security.authentication import get_current_user as _get
from app.models.user import User

async def get_current_user(user: User = Depends(_get)) -> User:
    return user
