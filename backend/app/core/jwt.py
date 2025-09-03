from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional, Sequence
from jose import jwt, JWTError
import uuid
from app.core.config import settings

# === Config ===
ALGORITHM = settings.jwt_algorithm
SECRET_KEY = settings.jwt_secret_key
ACCESS_TOKEN_EXPIRE_MINUTES = getattr(settings, "jwt_access_token_expire_minutes", 15)
ISSUER = "pos-backend"
AUDIENCE = "pos-frontend"

def _utcnow():
    return datetime.now(timezone.utc)

def create_access_token(
    data: dict,
    *,
    expires_delta: Optional[timedelta] = None,
    scopes: Optional[Sequence[str]] = None,
) -> str:
    to_encode = data.copy()
    exp = _utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({
        "exp": exp,
        "iat": _utcnow(),
        "nbf": _utcnow(),
        "iss": ISSUER,
        "aud": AUDIENCE,
        "type": "access",
        "jti": uuid.uuid4().hex,
        "scopes": list(scopes) if scopes else ["read"],
    })
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def create_refresh_token(data: dict, *, days: int = 30) -> str:
    to_encode = data.copy()
    exp = _utcnow() + timedelta(days=days)
    to_encode.update({
        "exp": exp,
        "iat": _utcnow(),
        "nbf": _utcnow(),
        "iss": ISSUER,
        "aud": AUDIENCE,
        "type": "refresh",
        "jti": uuid.uuid4().hex,
    })
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def decode_token(token: str, *, expected_type: Optional[str] = None) -> Optional[dict]:
    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
            audience=AUDIENCE,
            options={"require": ["exp", "iat", "nbf", "iss", "aud"]},
        )
        if expected_type and payload.get("type") != expected_type:
            return None
        return payload
    except JWTError:
        return None