# ================================================================
# EJEMPLO PRÁCTICO: Cómo el Sistema Determina Permisos
# ================================================================

"""
PREGUNTA: ¿Cómo sabe el sistema si puede leer o modificar en un endpoint?

RESPUESTA: A través de los decoradores @require_scope que validan permisos específicos.

Veamos el flujo PASO A PASO:
"""

# ================================================================
# PASO 1: El Token ya contiene los Scopes (desde el login)
# ================================================================

# Cuando el usuario hizo login, su token contiene algo así:
EJEMPLO_TOKEN_ADMIN = {
    "sub": "user_123",
    "scopes": ["read", "write", "read:products", "write:products", "admin", "read:users"],
    "exp": 1640995200
}

EJEMPLO_TOKEN_CAJERO = {
    "sub": "user_456", 
    "scopes": ["read", "read:products", "pos:sales"],
    "exp": 1640995200
}

# ================================================================
# PASO 2: Los Endpoints tienen Decoradores de Scope
# ================================================================

from fastapi import APIRouter
from app.core.oauth2_middleware import require_scope

router = APIRouter()

@router.get("/products/")
@require_scope("read:products")  # ← AQUÍ está la validación
async def get_products():
    """
    Este endpoint REQUIERE el scope 'read:products'
    """
    return {"message": "Lista de productos"}

@router.post("/products/")
@require_scope("write:products")  # ← AQUÍ está la validación
async def create_product():
    """
    Este endpoint REQUIERE el scope 'write:products'
    """
    return {"message": "Producto creado"}

@router.put("/products/{id}")
@require_scope("write:products")  # ← AQUÍ está la validación
async def update_product():
    """
    Este endpoint REQUIERE el scope 'write:products'
    """
    return {"message": "Producto actualizado"}

@router.delete("/products/{id}")
@require_scope("admin")  # ← Solo administradores pueden borrar
async def delete_product():
    """
    Este endpoint REQUIERE el scope 'admin'
    """
    return {"message": "Producto eliminado"}

# ================================================================
# PASO 3: La Validación Ocurre AUTOMÁTICAMENTE
# ================================================================

def require_scope(required_scope: str):
    """
    Este decorador se ejecuta ANTES de la función del endpoint
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # 1. Obtener el request (ya pasó por OAuth2Middleware)
            request = args[0]  # El primer argumento siempre es Request
            
            # 2. El token YA fue validado por OAuth2Middleware
            # Los scopes están en: request.state.token_payload
            token_scopes = request.state.token_payload.get('scopes', [])
            
            # 3. VALIDACIÓN: ¿El token tiene el scope requerido?
            if not has_required_scope(token_scopes, required_scope):
                # ❌ NO TIENE PERMISO
                raise HTTPException(
                    status_code=403,
                    detail=f"Acceso denegado. Necesitas: {required_scope}"
                )
            
            # ✅ SÍ TIENE PERMISO - Ejecutar la función
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator

def has_required_scope(token_scopes: list, required_scope: str) -> bool:
    """
    Lógica de validación de scopes
    """
    # Si es admin, puede hacer todo
    if "admin" in token_scopes:
        return True
    
    # Si no, debe tener el scope específico
    return required_scope in token_scopes

# ================================================================
# PASO 4: Ejemplos Prácticos de Validación
# ================================================================

# ESCENARIO 1: Administrador intenta crear producto
"""
1. Token contiene: ["admin", "read", "write", "read:products", "write:products"]
2. Endpoint requiere: "write:products"
3. Validación: "admin" in token_scopes? → SÍ
4. Resultado: ✅ PERMITIDO
"""

# ESCENARIO 2: Cajero intenta crear producto  
"""
1. Token contiene: ["read", "read:products", "pos:sales"]
2. Endpoint requiere: "write:products"
3. Validación: "admin" in token_scopes? → NO
4. Validación: "write:products" in token_scopes? → NO
5. Resultado: ❌ DENEGADO (HTTP 403)
"""

# ESCENARIO 3: Cajero intenta leer productos
"""
1. Token contiene: ["read", "read:products", "pos:sales"]
2. Endpoint requiere: "read:products"
3. Validación: "admin" in token_scopes? → NO
4. Validación: "read:products" in token_scopes? → SÍ
5. Resultado: ✅ PERMITIDO
"""

# ================================================================
# PASO 5: Flujo Completo de Request
# ================================================================

"""
FLUJO DETALLADO DE UN REQUEST:

1. 🌐 Cliente envía: GET /products/
   Headers: Authorization: Bearer eyJ0eXAiOiJKV1Qi...

2. 🛡️ OAuth2Middleware intercepta:
   - Extrae el token del header
   - Decodifica el JWT
   - Guarda scopes en request.state.token_payload
   - Continúa al endpoint

3. 🎯 Endpoint con @require_scope("read:products"):
   - El decorador se ejecuta ANTES de la función
   - Lee scopes desde request.state.token_payload
   - Valida: ¿"read:products" in scopes?
   - Si SÍ: ejecuta la función
   - Si NO: lanza HTTPException 403

4. 📊 Respuesta:
   - ✅ HTTP 200 + datos de productos
   - ❌ HTTP 403 + mensaje de error
"""

# ================================================================
# RESUMEN: ¿Cómo sabe el sistema qué puede hacer?
# ================================================================

"""
🔑 RESPUESTA SIMPLE:

1. El PERFIL/ROL se lee UNA SOLA VEZ (en el login)
2. Los SCOPES se calculan según el perfil y se guardan en el TOKEN
3. Cada ENDPOINT tiene un @require_scope("acción_específica")
4. El decorador VALIDA automáticamente si el token tiene ese scope
5. Si SÍ → ejecuta la función
6. Si NO → retorna error 403

NO hay consultas adicionales a la base de datos.
NO hay validaciones complejas.
Es simplemente: ¿El scope X está en la lista de scopes del token? SÍ/NO
"""

# ================================================================
# MAPEO DE PERMISOS ACTUAL EN TU SISTEMA
# ================================================================

PERMISOS_ENDPOINTS = {
    # PRODUCTOS
    "GET /products/": "read:products",      # Leer = Cajeros, Vendedores, Admins
    "POST /products/": "write:products",    # Crear = Solo Vendedores y Admins  
    "PUT /products/{id}": "write:products", # Editar = Solo Vendedores y Admins
    "DELETE /products/{id}": "admin",       # Borrar = Solo Administradores
    
    # USUARIOS
    "GET /users/": "read:users",            # Leer = Solo Admins y Managers
    "POST /users/": "write:users",          # Crear = Solo Administradores
    "PUT /users/{id}": "write:users",       # Editar = Solo Administradores
    
    # VENTAS
    "GET /sales/": "read:sales",            # Leer = Todos (según rol)
    "POST /sales/": "pos:sales",            # Crear venta = Cajeros y Vendedores
    "PUT /sales/{id}": "admin",             # Editar venta = Solo Admins
    
    # REPORTES
    "GET /reports/sales": "read:reports",       # Reportes básicos
    "GET /reports/advanced": "advanced:reports" # Reportes avanzados = Solo Admins
}
