# app/core/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import EmailStr

class Settings(BaseSettings):
    # lee .env.dev, ignora llaves desconocidas y no distingue mayúsculas/minúsculas
    model_config = SettingsConfigDict(
        env_file=".env.dev",
        case_sensitive=False,
        extra="ignore",
    )

    # DB
    async_database_url: str = "postgresql+asyncpg://user:1234566@localhost:5432/pointofsale"

    # JWT/OAuth
    jwt_secret_key: str = "your-super-secret-jwt-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 60
    oauth2_client_id: str = "frontend"
    oauth2_client_secret: str = "your-super-secret-client-secret-change-in-production"

    # Bootstrap admin (usa claves en MAYÚSCULA en el .env.dev)
    ADMIN_EMAIL: EmailStr = "admin@example.com"
    ADMIN_USERNAME: str = "admin"
    ADMIN_FULL_NAME: str = "Administrador"
    ADMIN_PASSWORD: str = "ChangeThis!"
    APP_ENV: str = "dev"
    ALLOWED_ORIGINS: str = ""
    
    MAX_IMPORT_ROWS: int = 1000  # leído desde .env
    
    
settings = Settings()