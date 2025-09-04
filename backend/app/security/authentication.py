from __future__ import annotations
from typing import Callable, Awaitable
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request, HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.jwt import decode_token
from app.core.security import get_async_db
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")
PUBLIC_PATHS: tuple[str, ...] = ("/openapi.json","/docs","/docs/oauth2-redirect","/redoc","/health","/auth/login","/auth/token")

class JWTAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable]):
        p = request.url.path
        if p in PUBLIC_PATHS or p.startswith("/public/") or (p == "/" and request.method == "GET"):
            return await call_next(request)
        auth = request.headers.get("Authorization","")
        parts = auth.split()
        if len(parts)!=2 or parts[0].lower()!="bearer":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing or invalid Authorization header")
        payload = decode_token(parts[1], expected_type="access")
        if not payload or "sub" not in payload:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")
        request.state.user_id = payload["sub"]
        request.state.scopes  = payload.get("scopes", [])
        return await call_next(request)

async def get_current_user(request: Request, db: AsyncSession = Depends(get_async_db)) -> User:
    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        token = await oauth2_scheme(request)
        payload = decode_token(token, expected_type="access")
        if not payload or "sub" not in payload:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or missing token")
        user_id = payload["sub"]
    user = (await db.execute(select(User).where(User.id==user_id))).scalar_one_or_none()
    if not user or not user.active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Inactive or missing user")
    return user
