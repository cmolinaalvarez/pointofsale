# ===========================================================
# async_session.py
# Configuración del motor de base de datos y la sesión asincrónica
# ===========================================================

# Importa herramientas necesarias para trabajar con SQLAlchemy de forma asíncrona:
# - `create_async_engine`: para conectar a la base de datos de forma asíncrona.
# - `async_sessionmaker`: para crear sesiones asincrónicas (para ejecutar consultas).
# - `AsyncSession`: clase base para trabajar con sesiones en modo async.
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

# Importa la configuración del archivo `config.py` (donde está la URL de conexión a la base de datos)
from app.core.config import settings

from typing import AsyncGenerator  # ✅ Importa esto para el tipo de retorno

# ===========================================================
# CREACIÓN DEL MOTOR DE BASE DE DATOS ASINCRÓNICO
# ===========================================================
# Este motor es responsable de administrar la conexión a la base de datos.
async_engine = create_async_engine(
    settings.async_database_url,  # URL de conexión cargada desde el archivo .env
    echo=True,                    # Si es True, muestra las consultas SQL en la consola (útil para depurar)
    future=True                   # Usa la API 2.0 de SQLAlchemy (recomendado)
)

# ===========================================================
# CREACIÓN DEL SESSIONMAKER ASINCRÓNICO
# ===========================================================
# `async_sessionmaker` se usa para generar sesiones asincrónicas que permiten
# interactuar con la base de datos sin bloquear el flujo del programa.
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,       # Asocia el sessionmaker al motor creado
    class_=AsyncSession,     # Usa la clase `AsyncSession` en lugar de la sesión tradicional
    expire_on_commit=False   # Si es False, los objetos no se invalidan tras hacer commit
)