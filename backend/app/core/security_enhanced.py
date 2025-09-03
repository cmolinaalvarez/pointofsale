from datetime import datetime, timedelta
from typing import Optional, List
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.core.security import get_async_db
from app.models.user import User
from app.crud.user import get_user_by_id
import logging

logger = logging.getLogger(__name__)

# Extender el esquema OAuth2 para incluir scopes
class OAuth2PasswordBearerWithScopes(OAuth2PasswordBearer):
    def __init__(self, tokenUrl: str, scopes: List[str] = None):
        super().__init__(tokenUrl=tokenUrl)
        self.required_scopes = scopes or []

oauth2_scheme = OAuth2PasswordBearerWithScopes(tokenUrl="auth/token")

class TokenBlacklist:
    def __init__(self):
        self.revoked_tokens = set()
    
    def add_token(self, token: str, expire_time: int):
        self.revoked_tokens.add((token, expire_time))
    
    def is_revoked(self, token: str) -> bool:
        current_time = datetime.utcnow().timestamp()
        # Limpiar tokens expirados
        self.revoked_tokens = {(t, exp) for t, exp in self.revoked_tokens if exp > current_time}
        return any(t == token for t, _ in self.revoked_tokens)

token_blacklist = TokenBlacklist()

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None, scopes: List[str] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({
        "exp": expire,
        "type": "access",
        "scopes": scopes or ["read"]  # Scopes por defecto
    })
    return jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_async_db)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        user_id: str = payload.get("sub")
        token_type: str = payload.get("type")
        
        if user_id is None or token_type != "access":
            raise credentials_exception
            
    except JWTError:
        raise credentials_exception
    
    # Verificar si el token está revocado
    if token_blacklist.is_revoked(token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token ha sido revocado"
        )
    
    user = await get_user_by_id(db, user_id)
    if user is None or not user.active:
        raise credentials_exception
    
    return user

def require_scope(required_scope: str):
    """Dependency para verificar scopes del token"""
    def scope_checker(token: str = Depends(oauth2_scheme)):
        try:
            payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
            token_scopes = payload.get("scopes", [])
            if required_scope not in token_scopes:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Permisos insuficientes"
                )
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido"
            )
        return token
    return scope_checker