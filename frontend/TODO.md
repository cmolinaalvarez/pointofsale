# 📋 TODO: Migración a estructura profesional

## 🎯 Objetivo: Implementar /api en el backend

### Backend (FastAPI):

1. Modificar `main.py` para montar rutas bajo `/api`:

   ```python
   from fastapi import FastAPI
   from fastapi.middleware.cors import CORSMiddleware

   app = FastAPI()

   # Configurar CORS
   app.add_middleware(CORSMiddleware, ...)

   # Montar API bajo /api
   api_router = APIRouter()
   api_router.include_router(auth_router, prefix="/auth")
   api_router.include_router(product_router, prefix="/products")

   app.include_router(api_router, prefix="/api")
   ```

2. Las rutas quedarían:
   - `/api/auth/login`
   - `/api/auth/register`
   - `/api/products`

### Frontend:

3. Remover métodos `getBackendUrl()` de los servicios
4. Usar directamente `this.apiUrl` que ya incluye `/api`

### ✅ Beneficios al completar:

- Estructura estándar de la industria
- Fácil versionado futuro (`/api/v1`, `/api/v2`)
- Mejor separación de responsabilidades
- Preparado para proxy y nginx en producción

### 🔧 Estado actual:

- Frontend: ✅ Configurado con `/api` (usando proxy temporal)
- Backend: ⏳ Pendiente migración a `/api`
