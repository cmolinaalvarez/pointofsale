# app/security/authentication.py
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

# endpoints de /auth permitidos sin token
_AUTH_PUBLIC = {"login", "token", "register", "refresh", "oauth2", "oauth2/info"}

# exactos sin token
_PUBLIC_EXACT = {
    "/", "/health", "/healthz",
    "/openapi.json", "/docs", "/docs/oauth2-redirect", "/redoc",
}

# prefijos sin token
_PUBLIC_PREFIXES = ("/public/", "/static/", "/assets/", "/docs/static/")

def _is_public(path: str, method: str) -> bool:
    # normaliza
    p = (path or "/").rstrip("/") or "/"
    if method in ("OPTIONS", "HEAD"):
        return True
    if p in _PUBLIC_EXACT or any(p.startswith(pref) for pref in _PUBLIC_PREFIXES):
        return True
    # /auth/* o /api/auth/* solo para endpoints permitidos
    if p.startswith("/auth/"):
        tail = p.removeprefix("/auth/")  # e.g. "register"
        return tail in _AUTH_PUBLIC
    if p.startswith("/api/auth/"):
        tail = p.removeprefix("/api/auth/")  # e.g. "register"
        return tail in _AUTH_PUBLIC
    return False

class JWTAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable]):
        path = request.scope.get("path", "/")
        if _is_public(path, request.method):
            return await call_next(request)

        auth = request.headers.get("Authorization", "")
        parts = auth.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing or invalid Authorization header")

        payload = decode_token(parts[1], expected_type="access")
        if not payload or "sub" not in payload:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

        request.state.user_id = payload["sub"]
        request.state.role = payload.get("role")
        scopes_raw = payload.get("scopes") or payload.get("scope") or []
        request.state.scopes = scopes_raw.split() if isinstance(scopes_raw, str) else list(scopes_raw)

        return await call_next(request)

# dependencia opcional
async def get_current_user(request: Request, db: AsyncSession = Depends(get_async_db)) -> User:
    from sqlalchemy import select
    uid = getattr(request.state, "user_id", None)
    if not uid:
        token = await oauth2_scheme(request)
        payload = decode_token(token, expected_type="access")
        if not payload or "sub" not in payload:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or missing token")
        uid = payload["sub"]
    user = (await db.execute(select(User).where(User.id == uid))).scalar_one_or_none()
    if not user or not user.active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Inactive or missing user")
    return user
