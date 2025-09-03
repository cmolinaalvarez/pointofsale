# ============================================================
# SCHEMAS DE AUTENTICACIÓN - Pydantic
# ============================================================
# Estos esquemas definen la forma de los datos que vamos a:
# - Recibir desde el cliente (inputs)
# - Enviar al cliente como respuesta (outputs)
# ============================================================

from pydantic import BaseModel, EmailStr  # EmailStr valida que sea un correo electrónico válido


# ============================================================
# ESQUEMA: TOKEN (respuesta al iniciar sesión o registrarse)
# ============================================================
class Token(BaseModel):
    access_token: str  # Aquí guardamos el JWT generado
    token_type: str = "bearer"  # Tipo de autenticación estándar ("bearer token" en encabezado HTTP)
    expires_in: int  # Tiempo de expiración en segundos


# ============================================================
# ESQUEMA: TokenData (útil para extraer datos del token JWT)
# ============================================================
class TokenData(BaseModel):
    user_id: int  # Guardamos el ID del usuario extraído del token (cuando se decodifica)


# ============================================================
# ESQUEMA: OAuth2 Token Request (estándar OAuth2)
# ============================================================
class OAuth2TokenRequest(BaseModel):
    grant_type: str = "password"  # Tipo de concesión OAuth2
    username: str  # Email del usuario (username en OAuth2)
    password: str  # Contraseña del usuario
    client_id: str  # ID del cliente (aplicación)
    client_secret: str  # Secreto del cliente


# ============================================================
# ESQUEMA: LoginRequest (cuando un usuario quiere iniciar sesión)
# ============================================================
class LoginRequest(BaseModel):
    email: EmailStr     # El usuario ingresa su correo
    password: str       # Y su contraseña


# ============================================================
# ESQUEMA: RegisterRequest (cuando un nuevo usuario se registra)
# ============================================================
class RegisterRequest(BaseModel):
    username: str
    email: EmailStr     # Email del nuevo usuario
    password: str       # Contraseña que se va a guardar (se encripta antes de guardar en DB)
