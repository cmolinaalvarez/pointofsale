from typing import Sequence
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.app.core.security import get_async_db
from backend.app.core.jwt import decode_token
from backend.app.models.user import User

oauth2 = OAuth2PasswordBearer(
    tokenUrl="/auth/token",
    scopes={
        "brands:read": "Leer marcas",
        "brands:write": "Crear/editar marcas",
    },
)

async def get_current_user(
    request: Request,
    token: str = Depends(oauth2),
    db: AsyncSession = Depends(get_async_db),
) -> User:
    payload = decode_token(token, expected_type="access")
    if not payload or not (uid := payload.get("sub")):
        raise HTTPException(status_code=401, detail="Token inválido")
    result = await db.execute(select(User).where(User.id == uid))
    user = result.scalars().first()
    if not user or getattr(user, "active", True) is False:
        raise HTTPException(status_code=401, detail="Usuario no encontrado o inactivo")
    request.state.user = user
    request.state.scopes = set(payload.get("scopes", []))
    return user

def require_scopes(required: Sequence[str]):
    async def _checker(request: Request, _user: User = Depends(get_current_user)):
        token_scopes = getattr(request.state, "scopes", set())
        if any(s not in token_scopes for s in required):
            raise HTTPException(status_code=403, detail="Permisos insuficientes")
        return True
    return _checker

async def current_user_id(request: Request) -> str:
    u: User | None = getattr(request.state, "user", None)
    if not u:
        raise HTTPException(status_code=401, detail="No autenticado")
    return str(u.id)
