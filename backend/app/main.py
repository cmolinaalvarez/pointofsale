# app/main.py
from __future__ import annotations

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.core.config import settings
from app.core.cors import setup_secure_cors
from app.core.errors import install_exception_handlers
from app.core.logging import setup_logging

from app.middleware.security_headers import SecurityHeadersMiddleware
from app.security.rate_limiting import limiter
from app.security.authentication import JWTAuthMiddleware
from app.security.input_validation import BodySanitizationMiddleware  # alias InputValidationMiddleware disponible

# --------------------------------------------------------------------
# Logging
# --------------------------------------------------------------------
setup_logging()
logger = logging.getLogger(__name__)

# --------------------------------------------------------------------
# App
# --------------------------------------------------------------------
app = FastAPI(
    title="API de Ventas - Sistema Punto de Venta",
    description="Backend para sistema de punto de venta con medidas de seguridad implementadas",
    version="1.0.0",
    docs_url="/docs" if settings.APP_ENV == "development" else None,
    redoc_url=None,
)

# --------------------------------------------------------------------
# CORS (outermost)
# --------------------------------------------------------------------
setup_secure_cors(app)

# Extra CORS en desarrollo (si hace falta)
if settings.APP_ENV == "development":
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://localhost:3001",
            "http://127.0.0.1:3001",
        ],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
        allow_headers=["*"],
    )

# --------------------------------------------------------------------
# Middlewares de seguridad (orden recomendado)
# --------------------------------------------------------------------
app.add_middleware(SecurityHeadersMiddleware)  # cabeceras seguras

# Sanitización / validación de JSON con parámetros
app.add_middleware(
    BodySanitizationMiddleware,
    max_body_bytes=2 * 1024 * 1024,  # 2 MB (puedes mover a settings)
    field_max={"code": 10, "name": 100, "description": 500, "basis": 20},
    # omitir endpoints que no son JSON o usan form-data (ej. login)
    skip_paths={"/api/auth/token", "/api/auth/login"},
)

app.add_middleware(JWTAuthMiddleware)          # auth JWT
app.add_middleware(SlowAPIMiddleware)          # rate limiting

# SlowAPI setup
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, lambda r, e: e.response)

# Excepciones custom
install_exception_handlers(app)

# --------------------------------------------------------------------
# Routers
# --------------------------------------------------------------------
from app.routers import (
    auth, user, brand, setting, category, subcategory, group, subgroup,
    unit, account, concept, document, country, division, municipality,
    product, warehouse, third_party, entry, purchase, payment_term, role,
)

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
    (role.router, "/api", "Roles"),
]

for router, prefix, tags in routers_config:
    app.include_router(router, prefix=prefix, tags=[tags])

# --------------------------------------------------------------------
# Health / root
# --------------------------------------------------------------------
@app.get("/")
async def root():
    return {
        "message": "API de Ventas - Backend funcionando correctamente",
        "version": "1.0.0",
        "docs": "/docs" if settings.APP_ENV == "development" else "Deshabilitado en producción",
    }

@app.get("/health")
@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "message": "Backend is running", "security": "enabled"}
