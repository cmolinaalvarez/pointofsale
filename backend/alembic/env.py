# ========================================================
# CONFIGURACIÓN DE MIGRACIONES ALEMBIC CON SQLALCHEMY ASYNC
# ========================================================

# Importamos herramientas de configuración de logs
from logging.config import fileConfig

# Importamos el sistema de pools (manejo de conexiones)
from sqlalchemy import pool

# Importamos el creador de motores asincrónicos a partir de configuración
from sqlalchemy.ext.asyncio import async_engine_from_config

# Importamos el contexto de Alembic, que permite controlar
# el modo offline, online, y ejecutar migraciones
from alembic import context

# Importamos nuestra configuración de entorno,
# que tiene la URL de conexión a la base de datos desde el archivo `.env`
from app.core.config import settings



# ========================================================
# CARGA LA CONFIGURACIÓN DEFINIDA EN alembic.ini
# ========================================================

# Obtenemos el objeto de configuración principal de Alembic
config = context.config

# Cargamos la configuración de logging desde alembic.ini
fileConfig(config.config_file_name)

# Sobrescribimos la URL de la base de datos con la definida en settings
# Esto hace que Alembic use la misma conexión que usamos en FastAPI
config.set_main_option("sqlalchemy.url", settings.async_database_url)


# ========================================================
# IMPORTAMOS LA METADATA DE LOS MODELOS
# ========================================================

# Importamos la clase Base que contiene los metadatos comunes
from app.db.base import Base

# Importamos explícitamente todos los modelos que queremos que Alembic detecte
# ⚠️ Si no importas un modelo, Alembic no lo verá en autogenerate
from app.models import user, role, brand, audit_log, setting, category, subcategory, group, subgroup, \
    unit, account, concept, document, country, division, municipality, product, warehouse, \
    third_party, purchase, entry, stock, payment_term, oauth2_client 
 
# Obtenemos los metadatos de los modelos ORM (tablas, columnas, etc.)
target_metadata = Base.metadata


# ========================================================
# MODO OFFLINE: SIN CONEXIÓN DIRECTA A LA BASE DE DATOS
# ========================================================

def run_migrations_offline():
    """
    Ejecuta las migraciones en modo offline (sin conectarse a la base de datos).
    En lugar de aplicar los cambios directamente, genera el SQL como texto.
    Útil para revisión manual o entornos donde no hay acceso directo a la DB.
    """
    context.configure(
        url=settings.async_database_url,      # URL de conexión a la base de datos
        target_metadata=target_metadata,      # Metadata de los modelos para detectar cambios
        literal_binds=True,                   # Inserta los valores literales directamente en el SQL generado
        dialect_opts={"paramstyle": "named"}, # Estilo de parámetros SQL
    )

    # Ejecutamos las migraciones dentro de una "transacción virtual"
    with context.begin_transaction():
        context.run_migrations()


# ========================================================
# MODO ONLINE: CONEXIÓN ASINCRÓNICA A LA BASE DE DATOS
# ========================================================

def run_migrations_online():
    """
    Ejecuta las migraciones directamente en la base de datos usando conexión asincrónica.
    Este modo se conecta realmente a la DB y aplica los cambios en tiempo real.
    """
    # Creamos el motor asincrónico de base de datos usando la configuración
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section),  # Obtiene sección [alembic] de alembic.ini
        prefix="sqlalchemy.",                           # Prefijo para claves como sqlalchemy.url
        poolclass=pool.NullPool                         # Evitamos el uso de pools de conexión (no necesario aquí)
    )

    # Esta función se ejecutará dentro de asyncio
    async def do_run_migrations():
        # Establece una conexión asincrónica con la base de datos
        async with connectable.connect() as connection:

            # Definimos una función interna que sí puede ser usada por Alembic (espera conexión sincrónica)
            def run_migrations(sync_connection):
                # Configuramos Alembic con esa conexión
                context.configure(
                    connection=sync_connection,
                    target_metadata=target_metadata
                )

                # Ejecutamos las migraciones dentro de una transacción
                with context.begin_transaction():
                    context.run_migrations()

            # Usamos run_sync para convertir la conexión async en una conexión compatible con Alembic
            await connection.run_sync(run_migrations)

    # Ejecutamos la migración usando asyncio
    import asyncio
    asyncio.run(do_run_migrations())


# ========================================================
# DECIDE AUTOMÁTICAMENTE SI USAR MODO OFFLINE U ONLINE
# ========================================================

# Si Alembic fue ejecutado con --sql, usamos modo offline
if context.is_offline_mode():
    run_migrations_offline()
# Si Alembic se ejecuta normalmente, usamos conexión directa a la base de datos
else:
    run_migrations_online()
