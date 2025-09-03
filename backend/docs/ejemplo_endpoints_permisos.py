# ================================================================
# EJEMPLO PRÁCTICO: Endpoints con Validación de Permisos
# ================================================================

"""
Este archivo muestra EXACTAMENTE cómo el sistema determina
si un usuario puede leer o modificar en cada endpoint.
"""

from fastapi import APIRouter, Request, HTTPException, Depends
from app.core.oauth2_middleware import require_scope

router = APIRouter()

# ================================================================
# EJEMPLO 1: Endpoints de Productos - Permisos Granulares
# ================================================================

@router.get("/products/")
@require_scope("read:products")  # ← PERMISO: Solo lectura de productos
async def get_products(request: Request):
    """
    ✅ PUEDEN ACCEDER:
    - Administradores (tienen "admin" scope)
    - Gerentes (tienen "read:products" scope) 
    - Empleados (tienen "read:products" scope)
    - Cajeros (tienen "read:products" scope)
    
    ❌ NO PUEDEN ACCEDER:
    - Usuarios sin token
    - Tokens sin scope "read:products"
    """
    # El sistema YA validó que el token tiene "read:products"
    # Aquí puedes acceder seguro a request.state.token_payload
    user_id = request.state.token_payload.get('sub')
    scopes = request.state.token_payload.get('scopes', [])
    
    print(f"👤 Usuario {user_id} con scopes {scopes} está leyendo productos")
    
    return {"message": "Lista de productos", "user": user_id}


@router.post("/products/")
@require_scope("write:products")  # ← PERMISO: Escritura de productos
async def create_product(request: Request):
    """
    ✅ PUEDEN ACCEDER:
    - Administradores (tienen "admin" scope - bypass automático)
    - Gerentes (tienen "write:products" scope)
    - Empleados (tienen "write:products" scope)
    
    ❌ NO PUEDEN ACCEDER:
    - Cajeros (solo tienen "read:products", NO "write:products")
    - Usuarios sin permisos de escritura
    """
    user_id = request.state.token_payload.get('sub')
    
    print(f"👤 Usuario {user_id} está CREANDO un producto")
    
    return {"message": "Producto creado", "created_by": user_id}


@router.delete("/products/{product_id}")
@require_scope("admin")  # ← PERMISO: Solo administradores
async def delete_product(product_id: str, request: Request):
    """
    ✅ PUEDEN ACCEDER:
    - Solo Administradores (tienen "admin" scope)
    
    ❌ NO PUEDEN ACCEDER:
    - Gerentes (no tienen "admin")
    - Empleados (no tienen "admin") 
    - Cajeros (no tienen "admin")
    """
    user_id = request.state.token_payload.get('sub')
    
    print(f"👤 Administrador {user_id} está ELIMINANDO producto {product_id}")
    
    return {"message": f"Producto {product_id} eliminado", "deleted_by": user_id}

# ================================================================
# EJEMPLO 2: Endpoints de Usuarios - Control Estricto
# ================================================================

@router.get("/users/")
@require_scope("read:users")  # ← PERMISO: Lectura de usuarios
async def get_users(request: Request):
    """
    ✅ PUEDEN ACCEDER:
    - Administradores (tienen "admin" scope)
    - Gerentes (tienen "read:users" scope)
    
    ❌ NO PUEDEN ACCEDER:
    - Empleados (no tienen "read:users")
    - Cajeros (no tienen "read:users")
    """
    return {"message": "Lista de usuarios (información sensible)"}


@router.post("/users/")
@require_scope("write:users")  # ← PERMISO: Crear usuarios
async def create_user(request: Request):
    """
    ✅ PUEDEN ACCEDER:
    - Solo Administradores (tienen "admin" scope)
    
    ❌ NO PUEDEN ACCEDER:
    - Gerentes (no tienen "write:users")
    - Empleados (no tienen "write:users")
    - Cajeros (no tienen "write:users")
    """
    return {"message": "Usuario creado"}

# ================================================================
# EJEMPLO 3: Endpoints de Ventas - Permisos Especializados
# ================================================================

@router.get("/sales/")
@require_scope("read:sales")  # ← PERMISO: Lectura de ventas
async def get_sales(request: Request):
    """
    ✅ PUEDEN ACCEDER:
    - Administradores (scope "admin")
    - Gerentes (scope "read:sales")
    - Empleados (scope "read:sales")
    - Cajeros (scope "read:sales")
    """
    return {"message": "Lista de ventas"}


@router.post("/sales/")
@require_scope("pos:sales")  # ← PERMISO: Crear ventas (POS)
async def create_sale(request: Request):
    """
    ✅ PUEDEN ACCEDER:
    - Administradores (scope "admin")
    - Empleados (scope "pos:sales")
    - Cajeros (scope "pos:sales")
    
    ❌ NO PUEDEN ACCEDER:
    - Gerentes (no tienen "pos:sales", solo leen reportes)
    """
    return {"message": "Venta creada"}

# ================================================================
# EJEMPLO 4: ¿Cómo se Ejecuta la Validación?
# ================================================================

"""
FLUJO PASO A PASO cuando llega un request:

1. 🌐 Cliente envía: POST /products/
   Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...

2. 🛡️ OAuth2Middleware (se ejecuta AUTOMÁTICAMENTE):
   - Extrae: "Bearer eyJ0eXAi..."
   - Decodifica JWT: {"sub": "user_123", "scopes": ["read", "write:products"]}
   - Guarda en: request.state.token_payload = {...}

3. 🎯 @require_scope("write:products") (se ejecuta ANTES del endpoint):
   - Lee: token_scopes = request.state.token_payload['scopes']
   - Valida: ¿"write:products" in ["read", "write:products"]? → SÍ
   - Resultado: ✅ CONTINÚA al endpoint

4. 📊 create_product() (se ejecuta FINALMENTE):
   - Ya sabemos que el usuario TIENE permisos
   - Ejecuta la lógica de negocio
   - Retorna respuesta exitosa

PERO si fuera un cajero con scopes ["read", "read:products", "pos:sales"]:
   - Valida: ¿"write:products" in ["read", "read:products", "pos:sales"]? → NO
   - Resultado: ❌ HTTPException 403 Forbidden
   - ¡NUNCA llega al endpoint!
"""

# ================================================================
# MAPEO COMPLETO DE PERMISOS EN TU SISTEMA
# ================================================================

MAPA_PERMISOS = {
    "ADMINISTRADOR": {
        "scopes": ["admin", "read", "write", "read:products", "write:products", 
                  "read:users", "write:users", "read:sales", "pos:sales", 
                  "read:reports", "advanced:reports"],
        "puede_hacer": [
            "✅ Leer productos", "✅ Crear productos", "✅ Editar productos", "✅ Eliminar productos",
            "✅ Leer usuarios", "✅ Crear usuarios", "✅ Editar usuarios", 
            "✅ Leer ventas", "✅ Crear ventas", "✅ Editar ventas",
            "✅ Ver reportes básicos", "✅ Ver reportes avanzados"
        ]
    },
    
    "GERENTE": {
        "scopes": ["read", "write", "read:products", "write:products", 
                  "read:users", "read:sales", "read:reports"],
        "puede_hacer": [
            "✅ Leer productos", "✅ Crear productos", "✅ Editar productos", "❌ Eliminar productos",
            "✅ Leer usuarios", "❌ Crear usuarios", "❌ Editar usuarios",
            "✅ Leer ventas", "❌ Crear ventas", "❌ Editar ventas", 
            "✅ Ver reportes básicos", "❌ Ver reportes avanzados"
        ]
    },
    
    "EMPLEADO": {
        "scopes": ["read", "read:products", "write:products", "pos:sales", "read:sales"],
        "puede_hacer": [
            "✅ Leer productos", "✅ Crear productos", "✅ Editar productos", "❌ Eliminar productos",
            "❌ Leer usuarios", "❌ Crear usuarios", "❌ Editar usuarios",
            "✅ Leer ventas", "✅ Crear ventas", "❌ Editar ventas",
            "❌ Ver reportes", "❌ Ver reportes avanzados"
        ]
    },
    
    "CAJERO": {
        "scopes": ["read", "read:products", "pos:sales", "read:sales"],
        "puede_hacer": [
            "✅ Leer productos", "❌ Crear productos", "❌ Editar productos", "❌ Eliminar productos",
            "❌ Leer usuarios", "❌ Crear usuarios", "❌ Editar usuarios",
            "✅ Leer ventas", "✅ Crear ventas", "❌ Editar ventas",
            "❌ Ver reportes", "❌ Ver reportes avanzados"
        ]
    }
}

# ================================================================
# RESPUESTA FINAL: ¿Cómo sabe el sistema si puede leer/modificar?
# ================================================================

"""
🎯 RESPUESTA DIRECTA:

1. 🔑 CADA ENDPOINT tiene un @require_scope("acción_específica")
2. 🛡️ El decorador extrae los scopes del TOKEN (ya decodificado)
3. ✅ Si el scope requerido está en el token → PERMITE el acceso
4. ❌ Si el scope requerido NO está en el token → BLOQUEA con error 403

EJEMPLOS CONCRETOS:
- GET /products/ requiere "read:products" → Cajeros SÍ pueden
- POST /products/ requiere "write:products" → Cajeros NO pueden  
- DELETE /products/{id} requiere "admin" → Solo Administradores pueden

Es un sistema de PERMISOS GRANULARES donde cada acción específica
tiene su propio permiso, y el token del usuario determina qué puede hacer.

¡NO hay consultas a la base de datos en cada request!
¡TODO está en el token desde el login!
"""
