from fastapi import APIRouter, Depends, HTTPException, status, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.security import get_async_db
from app.schemas.user import UserRead
from app.models.user import User
from app.schemas.auth import Token, LoginRequest, RegisterRequest
from app.core.security import verify_password, get_password_hash
from app.dependencies.current_user import get_current_user
from app.core.jwt import create_access_token, create_refresh_token, decode_token, ACCESS_TOKEN_EXPIRE_MINUTES
from app.core.config import settings
router = APIRouter(tags=["Authentication"])
 

@router.post("/register", response_model=Token, status_code=201)
async def register(data: RegisterRequest, db: AsyncSession = Depends(get_async_db)):
    email = data.email.strip().lower()
    result = await db.execute(select(User).where(User.email == email))
    existing_user = result.scalars().first()
    new_user = User(
        username=data.username.strip(),
        email=email,
        full_name=data.username.strip(),
        password=await get_password_hash(data.password),
        active=True,
        superuser=False,
    )
    db.add(new_user)
    await db.flush()         # asigna PK en memoria cuando aplique
    await db.refresh(new_user)
    await db.commit()
    access = create_access_token({"sub": str(new_user.id)})
    refresh = create_refresh_token({"sub": str(new_user.id)})
    return {
        "access_token": access,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "refresh_token": refresh,
    }

@router.post("/token", response_model=Token)
async def oauth2_token(
    grant_type: str = Form(...),
    username: str = Form(...),  # En OAuth2, username puede ser email
    password: str = Form(...),
    client_id: str = Form(...),
    client_secret: str = Form(...),
    scope: str = Form("read"),  # scopes solicitados (separados por espacios)
    db: AsyncSession = Depends(get_async_db)
    ):

    if grant_type != "password":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="grant_type no soportado. Use 'password'"
        )

    if client_id != settings.oauth2_client_id or client_secret != settings.oauth2_client_secret:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales del cliente inválidas",
            headers={"WWW-Authenticate": "Bearer"},
        ) 

    stmt = select(User).where(User.email == username.strip().lower())
    result = await db.execute(stmt)
    user = result.scalars().first() 

    if not user or not await verify_password(password, user.password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciales de usuario inválidas",
                headers={"WWW-Authenticate": "Bearer"},
            )
    if hasattr(user, "active") and not user.active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Usuario inactivo")

    # Scopes: evita dependencias no definidas (ScopeValidator/get_scopes_for_user_role)
    requested_scopes = [s for s in scope.split() if s]
    allowed_by_role = {"read"}  # mínimo
    if getattr(user, "superuser", False):
        allowed_by_role.update({"write", "delete", "admin", "read:products", "write:products", "read:users", "write:users"})
    final_scopes = [s for s in requested_scopes if s in allowed_by_role] or ["read"]

    access = create_access_token(data={"sub": str(user.id)}, scopes=final_scopes)
    refresh = create_refresh_token(data={"sub": str(user.id)})
    return {
        "access_token": access,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "refresh_token": refresh,
        "scope": " ".join(final_scopes),
    }

@router.post("/login", response_model=Token)
async def login(data: LoginRequest, db: AsyncSession = Depends(get_async_db)):

    stmt = select(User).where(User.email == data.email.strip().lower())
    result = await db.execute(stmt)
    user = result.scalars().first()

    if not user or not await verify_password(data.password, user.password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciales inválidas"
            )
    if hasattr(user, "active") and not user.active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Usuario inactivo")

    token = create_access_token({"sub": str(user.id)})
    access = create_access_token({"sub": str(user.id)})
    refresh = create_refresh_token({"sub": str(user.id)})

    return {
        "access_token": access,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "refresh_token": refresh,
    }

@router.post("/logout")
async def logout():

    return {"message": "Sesión cerrada correctamente. Por favor elimina el token en el cliente."}

@router.get("/me", response_model=UserRead)
async def read_me(current: User = Depends(get_current_user)):
    return current

@router.get("/oauth2/info")
async def oauth2_info():

    return {
        "grant_types_supported": ["password"],
        "token_endpoint": "/auth/token",
        "scopes_supported": [
            "read",
            "write", 
            "delete",
            "admin",
            "read:products",
            "write:products",
            "read:users",
            "write:users"
        ],
        "token_endpoint_auth_methods_supported": ["client_secret_post"],
        "client_id_required": True,
        "client_secret_required": True
    }

@router.post("/refresh", response_model=Token)
async def refresh_token(refresh_token: str = Form(...), client_id: str = Form(None), client_secret: str = Form(None)):
    # Opcional: exige validación de cliente si pasas client creds
    if client_id or client_secret:
        if client_id != settings.oauth2_client_id or client_secret != settings.oauth2_client_secret:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Cliente no autorizado")
    payload = decode_token(refresh_token, expected_type="refresh")
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token inválido")
    user_id = payload.get("sub")
    access = create_access_token({"sub": str(user_id)})
    return {
        "access_token": access,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }
