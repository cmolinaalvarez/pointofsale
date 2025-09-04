# ========================================================================
# Importaciones necesarias
# ========================================================================

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.middleware.security_middleware import SecurityMiddleware
from app.core.cors import setup_secure_cors
from app.core.config import settings
from app.utils.logging_config import setup_logging
import logging

# ========================================================================
# Configuración inicial
# ========================================================================

# Configuración de logging
setup_logging()
logger = logging.getLogger(__name__)

# ========================================================================
# Crear la instancia principal de la aplicación
# ========================================================================

app = FastAPI(
    title="API de Ventas - Sistema Punto de Venta",
    description="Backend para sistema de punto de venta con medidas de seguridad implementadas",
    version="1.0.0",
    docs_url="/docs" if settings.APP_ENV == "development" else None,
    redoc_url=None,
)

# ========================================================================
# Middlewares de seguridad y CORS
# ========================================================================

# 1. Middleware de seguridad personalizado
app.add_middleware(SecurityMiddleware)

# 2. Configurar CORS seguro (usando la función personalizada)
setup_secure_cors(app)

# 3. CORS adicional para desarrollo (puedes eliminar esto si setup_secure_cors es suficiente)
if settings.APP_ENV == "development":
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:3000",
            "http://127.0.0.1:3000", 
            "http://localhost:3001",
            "http://127.0.0.1:3001"
        ],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )

# ========================================================================
# Importar y registrar routers
# ========================================================================

from app.routers import (
    auth, user, brand, setting, category, subcategory, group, subgroup,
    unit, account, concept, document, country, division, municipality,
    product, warehouse, third_party, entry, purchase, payment_term, role
)

# Lista organizada de routers con sus prefijos
routers_config = [
    (auth.router, "/api/auth", "Authentication"),
    (user.router, "/api/users", "Users"),
    (brand.router, "/api", "Brands"),
    (setting.router, "/api", "Settings"),
    (category.router, "/api", "Categories"),
    (subcategory.router, "/api", "SubCategories"),
    (group.router, "/api", "Groups"),
    (subgroup.router, "/api", "SubGroups"),
    (unit.router, "/api", "Units"),
    (account.router, "/api", "Accounts"),
    (concept.router, "/api", "Concepts"),
    (document.router, "/api", "Documents"),
    (country.router, "/api", "Countries"),
    (division.router, "/api", "Divisions"),
    (municipality.router, "/api", "Municipalities"),
    (product.router, "/api", "Products"),
    (warehouse.router, "/api", "Warehouses"),
    (third_party.router, "/api", "ThirdParties"),
    (entry.router, "/api/entries", "Entries"),
    (purchase.router, "/api/purchases", "Purchases"),
    (payment_term.router, "/api", "PaymentTerms"),
    (role.router, "/api", "Roles")
]

# Registrar todos los routers
for router, prefix, tags in routers_config:
    app.include_router(router, prefix=prefix, tags=[tags])

# ========================================================================
# Endpoints básicos de salud y raíz
# ========================================================================

@app.get("/")
async def root():
    """Endpoint raíz - Información básica de la API"""
    return {
        "message": "API de Ventas - Backend funcionando correctamente",
        "version": "1.0.0",
        "docs": "/docs" if settings.APP_ENV == "development" else "Deshabilitado en producción"
    }

@app.get("/health")
@app.get("/api/health")
async def health_check():
    """Endpoint para verificar que el servidor está funcionando"""
    return {
        "status": "healthy", 
        "message": "Backend is running",
        "security": "enabled"
    }

# ========================================================================
# Configuración adicional para entornos específicos
# ========================================================================

if settings.APP_ENV == "development":
    @app.get("/debug/info")
    async def debug_info():
        """Endpoint de debug solo disponible en desarrollo"""
        return {
            "environment": settings.APP_ENV,
            "debug": True,
            "allowed_origins": settings.ALLOWED_ORIGINS.split(',') if hasattr(settings, 'ALLOWED_ORIGINS') else []
        }