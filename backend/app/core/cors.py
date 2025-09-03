from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings

def setup_secure_cors(app):
    """
    Configuración segura de CORS
    """
    # Obtener origenes permitidos desde settings
    allowed_origins = getattr(settings, 'ALLOWED_ORIGINS', '').split(',')
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
        allow_headers=[
            "Authorization",
            "Content-Type",
            "X-Requested-With",
            "X-CSRF-Token"
        ],
        expose_headers=["Content-Range", "X-Total-Count"],
        max_age=600,  # 10 minutos para preflight requests
    )