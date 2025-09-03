# 🔐 OAuth2 con Scopes - Explicación Completa del Proceso

## 📋 **Resumen Ejecutivo**

El sistema OAuth2 implementado permite que **diferentes tipos de clientes** (aplicaciones) accedan al sistema con **diferentes niveles de permisos** (scopes). Esto garantiza que cada aplicación solo tenga acceso a las funcionalidades que realmente necesita.

## 🎯 **Conceptos Clave**

### **1. Clientes OAuth2**

Son aplicaciones registradas que pueden solicitar tokens de acceso:

- **Frontend Web**: Aplicación completa de administración
- **Mobile App**: App móvil para punto de venta
- **Reports API**: Sistema externo para reportes
- **Third Party**: Integraciones de solo lectura

### **2. Scopes (Alcances)**

Son permisos específicos que definen qué puede hacer cada token:

- `read:products` → Solo consultar productos
- `write:products` → Crear/modificar productos
- `pos:sales` → Operaciones de punto de venta
- `admin` → Acceso administrativo completo

### **3. Tokens JWT**

Contienen la información del usuario y sus permisos:

```json
{
  "sub": "user_id_123",
  "scopes": ["read", "write:products", "pos:sales"],
  "exp": 1640995200
}
```

## 🔄 **Proceso Detallado**

### **Paso 1: Registro de Cliente OAuth2**

```sql
INSERT INTO oauth2_clients (
  client_id: "frontend_web_v1_abc123",
  client_secret: "hashed_secret",
  allowed_scopes: ["read", "write", "read:products", "write:products"],
  active: true
)
```

### **Paso 2: Solicitud de Token**

```http
POST /auth/token
Content-Type: application/x-www-form-urlencoded

grant_type=password
username=user@test.com
password=123456
client_id=frontend_web_v1_abc123
client_secret=web_secret_123
scope=read write read:products write:products
```

### **Paso 3: Validación del Servidor**

1. **Validar cliente**: ¿Existe el `client_id` y `client_secret`?
2. **Validar usuario**: ¿Son correctas las credenciales del usuario?
3. **Validar scopes**: ¿El cliente puede solicitar estos scopes?
4. **Asignar scopes**: Solo aprobar scopes válidos y permitidos

### **Paso 4: Generación de Token**

```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "expires_in": 3600,
  "scopes": ["read", "write:products"]
}
```

### **Paso 5: Uso del Token**

```http
GET /products/
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

### **Paso 6: Validación en Endpoint**

```python
@router.get("/products/")
@require_scope("read:products")  # ← Validación automática
async def list_products():
    # Solo se ejecuta si el token tiene "read:products"
```

## 📊 **Ejemplos Prácticos**

### **🖥️ Caso 1: Frontend Web (Permisos Completos)**

```
Usuario: Administrador
Cliente: frontend_web_v1
Scopes: ["read", "write", "read:products", "write:products", "admin"]

✅ Puede: Consultar productos, crear productos, gestionar usuarios
❌ No puede: Generar reportes avanzados (no tiene scope "advanced:reports")
```

### **📱 Caso 2: Mobile App (Permisos Limitados)**

```
Usuario: Cajero
Cliente: mobile_pos_v1
Scopes: ["read", "read:products", "pos:sales"]

✅ Puede: Consultar productos, procesar ventas en POS
❌ No puede: Crear productos, gestionar usuarios, acceder a reportes
```

### **📊 Caso 3: Reports API (Especializado)**

```
Usuario: Sistema automático
Cliente: reports_api_v1
Scopes: ["read:reports", "advanced:reports", "export:reports"]

✅ Puede: Generar reportes, exportar datos, análisis avanzados
❌ No puede: Modificar productos, procesar ventas, gestionar usuarios
```

## 🛡️ **Seguridad y Validación**

### **Validación Automática**

Cada endpoint protegido valida automáticamente:

1. ¿El token es válido y no ha expirado?
2. ¿El token contiene el scope requerido?
3. ¿El usuario tiene permisos para este scope?

### **Respuestas de Error**

```json
// Token inválido
HTTP 401: "Token de autorización requerido"

// Scope insuficiente
HTTP 403: "Acceso denegado. Scope requerido: write:products"

// Cliente inválido
HTTP 401: "Credenciales del cliente inválidas"
```

## 🔧 **Configuración Dinámica**

### **Agregar Nuevo Cliente**

```http
POST /oauth2/clients/
{
  "name": "Warehouse Mobile App",
  "description": "App móvil para gestión de inventario",
  "allowed_scopes": ["read", "read:inventory", "write:inventory"],
  "allowed_grant_types": ["password"]
}
```

### **Modificar Scopes de Cliente**

```http
PUT /oauth2/clients/warehouse_mobile_v1
{
  "allowed_scopes": ["read", "read:inventory", "write:inventory", "transfer:inventory"]
}
```

## 📈 **Beneficios del Sistema**

### **🔐 Seguridad**

- **Principio de menor privilegio**: Cada cliente solo tiene permisos mínimos
- **Tokens específicos**: Un token comprometido tiene acceso limitado
- **Validación granular**: Control fino sobre cada operación

### **📱 Flexibilidad**

- **Clientes especializados**: Apps móviles, APIs externas, sistemas de reportes
- **Scopes configurables**: Fácil agregar nuevos permisos
- **Escalabilidad**: Soporta múltiples tipos de aplicaciones

### **🔧 Mantenibilidad**

- **Configuración centralizada**: Todos los scopes en un lugar
- **Auditoría automática**: Log de todos los accesos
- **APIs RESTful**: Gestión completa de clientes OAuth2

## 🚀 **Casos de Uso Reales**

1. **E-commerce Multi-canal**

   - Web admin: Scopes completos
   - App móvil: Solo ventas
   - API partners: Solo consultas

2. **Sistema ERP**

   - Admin panel: Todos los módulos
   - Módulo contable: Solo finanzas
   - Reportes BI: Solo lectura analítica

3. **Marketplace**
   - Vendedores: Sus productos
   - Compradores: Solo compras
   - Administradores: Gestión completa

## ⚡ **Próximos Pasos**

1. **Implementar scopes** en todos los endpoints restantes
2. **Crear clientes específicos** para cada aplicación
3. **Configurar monitoreo** de uso de scopes
4. **Implementar rate limiting** por tipo de cliente
5. **Agregar scopes dinámicos** basados en roles de usuario

---

> 💡 **Este sistema OAuth2 con scopes proporciona una base sólida y escalable para controlar el acceso a tu API, permitiendo diferentes niveles de integración según las necesidades específicas de cada cliente.**
