# ================================================================
# MÓDULO DE SEGURIDAD
# - Maneja hashing de contraseñas y verificación segura.
# - Obtiene el usuario actual desde el token (asincrónicamente).
# - Prepara sesiones de base de datos asincrónicas.
# ================================================================

# ---------------------------------------------------------------
# Importamos tipos para anotación de funciones asincrónicas
# ---------------------------------------------------------------
from typing import AsyncGenerator

# ---------------------------------------------------------------
# Clase base para sesiones asincrónicas de SQLAlchemy
# ---------------------------------------------------------------
from sqlalchemy.ext.asyncio import AsyncSession

# ---------------------------------------------------------------
# Importamos nuestro sessionmaker asincrónico personalizado
# ---------------------------------------------------------------
from app.db.async_session import AsyncSessionLocal

# ---------------------------------------------------------------
# Importamos CryptContext de Passlib para hashing de contraseñas
# ---------------------------------------------------------------
from passlib.context import CryptContext

# ---------------------------------------------------------------
# Función estándar de asyncio para ejecutar código bloqueante
# en un hilo separado, sin bloquear el event loop principal
# ---------------------------------------------------------------
import asyncio

# ================================================================
# DEPENDENCIA PARA BASE DE DATOS ASINCRÓNICA
# - Usada en endpoints y servicios para obtener una sesión válida
# - Se cierra automáticamente después del uso
# ================================================================
async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session
        # La sesión se cierra automáticamente al salir del bloque

# ================================================================
# CONTEXTO DE HASHING DE CONTRASEÑAS
# - Usa bcrypt (recomendado por OWASP)
# - Configura el esquema para hashear y verificar
# ================================================================
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ================================================================
# FUNCIONES ASÍNCRONAS PARA HASHING DE CONTRASEÑAS
# - Usan asyncio.to_thread para evitar bloquear el event loop
# ================================================================

async def get_password_hash(password: str) -> str:
    """
    Devuelve el hash seguro de la contraseña.
    Ejecutado en un hilo separado para no bloquear el event loop.
    """
    return await asyncio.to_thread(pwd_context.hash, password)

async def verify_password(plain_password: str, password: str) -> bool:
    """
    Verifica que la contraseña en texto plano coincida con el hash.
    Ejecutado en un hilo separado para no bloquear el event loop.
    """
    return await asyncio.to_thread(pwd_context.verify, plain_password, password)