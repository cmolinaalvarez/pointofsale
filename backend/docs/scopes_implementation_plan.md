"""
Plan de Implementación Completa de Scopes
==========================================

# ENDPOINTS PENDIENTES DE PROTEGER:

1. PRODUCTOS (completar):

   - DELETE /products/{id} → require_scope("delete:products")
   - PATCH /products/{id} → require_scope("write:products")
   - POST /products/import → require_scope("import:products")

2. USUARIOS (completar):

   - PUT /users/{id} → require_scope("write:users")
   - PATCH /users/{id} → require_scope("write:users")
   - DELETE /users/{id} → require_scope("admin")

3. COMPRAS (completar):

   - GET /purchases/ → require_scope("read:purchases")
   - GET /purchases/{id} → require_scope("read:purchases")
   - PUT /purchases/{id} → require_scope("write:purchases")
   - DELETE /purchases/{id} → require_scope("delete:purchases")
   - POST /purchases/import → require_scope("import:purchases")

4. OTROS MÓDULOS:
   - Brands: read:products, write:products
   - Categories: read:products, write:products
   - Warehouses: read:inventory, write:inventory
   - Countries/Municipalities: read:system, write:system
   - Concepts: read:system, write:system
   - Documents: read:system, write:system

# ENDPOINTS RECOMENDADOS PARA IMPLEMENTAR:

@router.get("/brands/")
@require_scope("read:products")

@router.post("/brands/")
@require_scope("write:products")

@router.get("/categories/")
@require_scope("read:products")

@router.post("/categories/")
@require_scope("write:products")

@router.get("/warehouses/")
@require_scope("read:inventory")

@router.post("/warehouses/")
@require_scope("write:inventory")

# CONFIGURACIÓN DE CLIENTES OAUTH2:

Para diferentes tipos de aplicaciones:

1. Frontend Web Completo:
   allowed_scopes: ["read", "write", "read:products", "write:products",
   "read:purchases", "write:purchases", "read:users"]

2. App Móvil (Solo Ventas):
   allowed_scopes: ["read", "read:products", "pos:sales", "write:sales"]

3. API Externa (Solo Lectura):
   allowed_scopes: ["read", "read:products", "read:sales", "read:inventory"]

4. Sistema de Reportes:
   allowed_scopes: ["read", "read:reports", "advanced:reports", "export:reports"]

# PRÓXIMOS PASOS:

1. Aplicar @require_scope a todos los endpoints restantes
2. Crear clientes OAuth2 específicos para cada tipo de aplicación
3. Implementar middleware de logging para auditar uso de scopes
4. Crear endpoint de documentación de scopes disponibles
5. Implementar scopes dinámicos basados en roles de usuario

# TESTING:

Para probar los scopes:

1. Crear cliente OAuth2 con scopes limitados
2. Obtener token con scopes específicos
3. Intentar acceder a endpoints con diferentes scopes
4. Verificar que se deniegue acceso apropiadamente

curl -X POST "http://localhost:8000/auth/token" \
 -H "Content-Type: application/x-www-form-urlencoded" \
 -d "grant_type=password&username=test@test.com&password=123456&client_id=your_client&client_secret=your_secret&scope=read read:products"

"""
