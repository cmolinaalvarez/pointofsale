-- =====================================================
-- SCRIPT SQL: INSERCIÓN DE 10 PERFILES PROFESIONALES
-- Sistema de Ventas - Roles y Permisos
-- ESPECÍFICAMENTE OPTIMIZADO PARA POSTGRESQL
-- =====================================================

-- Habilitar extensión para UUIDs (solo si no está habilitada)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Limpiar datos previos (opcional - descomenta si necesitas reset completo)
-- TRUNCATE TABLE user_roles RESTART IDENTITY CASCADE;
-- TRUNCATE TABLE roles RESTART IDENTITY CASCADE;

-- =====================================================
-- INSERCIÓN DE 10 ROLES PROFESIONALES
-- =====================================================

BEGIN;

-- 1. SUPERADMIN - Administrador Completo del Sistema
INSERT INTO roles (
    id, code, name, description, role_type, permissions, priority_level, 
    active, is_system_role, created_at, updated_at
) VALUES (
    gen_random_uuid(),
    'SUPERADMIN',
    'Super Administrador',
    'Acceso completo al sistema, puede gestionar todo incluyendo configuraciones críticas',
    'admin',
    '{"scopes": ["admin", "read", "write", "delete", "read:users", "write:users", "delete:users", "read:products", "write:products", "delete:products", "read:sales", "write:sales", "delete:sales", "pos:sales", "read:purchases", "write:purchases", "delete:purchases", "read:inventory", "write:inventory", "adjust:inventory", "read:reports", "advanced:reports", "export:reports", "read:settings", "write:settings", "read:audit", "write:audit", "manage:system", "backup:system", "read:roles", "write:roles", "assign:roles"], "special_permissions": {"can_delete_transactions": true, "can_modify_prices": true, "can_access_all_warehouses": true, "can_override_discounts": true, "max_discount_percent": 100}}'::JSONB,
    1,
    true,
    true,
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
);

-- 2. GERENTE_GENERAL - Gerente General
INSERT INTO roles (
    id, code, name, description, role_type, permissions, priority_level, 
    active, is_system_role, created_at, updated_at
) VALUES (
    gen_random_uuid(),
    'GERENTE_GENERAL',
    'Gerente General',
    'Gestión completa del negocio, reportes ejecutivos y supervisión de operaciones',
    'manager',
    '{"scopes": ["read", "write", "read:users", "write:users", "read:products", "write:products", "read:sales", "write:sales", "pos:sales", "read:purchases", "write:purchases", "read:inventory", "write:inventory", "read:reports", "advanced:reports", "export:reports", "read:settings", "read:audit", "read:roles", "assign:roles"], "special_permissions": {"can_modify_prices": true, "can_access_all_warehouses": true, "can_override_discounts": true, "max_discount_percent": 50, "can_view_financial_reports": true}}'::JSONB,
    2,
    true,
    true,
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
);

-- 3. GERENTE_VENTAS - Gerente de Ventas
INSERT INTO roles (
    id, code, name, description, role_type, permissions, priority_level, 
    active, is_system_role, created_at, updated_at
) VALUES (
    gen_random_uuid(),
    'GERENTE_VENTAS',
    'Gerente de Ventas',
    'Gestión del equipo de ventas, metas, comisiones y reportes comerciales',
    'manager',
    '{"scopes": ["read", "write", "read:users", "read:products", "write:products", "read:sales", "write:sales", "pos:sales", "read:inventory", "read:reports", "advanced:reports", "read:settings"], "special_permissions": {"can_modify_prices": true, "can_manage_sales_team": true, "can_set_sales_targets": true, "max_discount_percent": 30, "can_view_sales_reports": true}}'::JSONB,
    3,
    true,
    true,
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
);

-- 4. CONTADOR - Contabilidad
INSERT INTO roles (
    id, code, name, description, role_type, permissions, priority_level, 
    active, is_system_role, created_at, updated_at
) VALUES (
    gen_random_uuid(),
    'CONTADOR',
    'Contador/Contabilidad',
    'Gestión contable, reportes financieros, cuentas por pagar y cobrar',
    'employee',
    '{"scopes": ["read", "read:users", "read:products", "read:sales", "read:purchases", "write:purchases", "read:inventory", "read:reports", "advanced:reports", "export:reports", "read:audit"], "special_permissions": {"can_view_financial_reports": true, "can_manage_accounts": true, "can_generate_tax_reports": true, "can_view_all_transactions": true}}'::JSONB,
    3,
    true,
    true,
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
);

-- 5. JEFE_ALMACEN - Jefe de Almacén
INSERT INTO roles (
    id, code, name, description, role_type, permissions, priority_level, 
    active, is_system_role, created_at, updated_at
) VALUES (
    gen_random_uuid(),
    'JEFE_ALMACEN',
    'Jefe de Almacén',
    'Gestión completa de inventarios, compras, stocks y almacenes',
    'supervisor',
    '{"scopes": ["read", "write", "read:products", "write:products", "read:purchases", "write:purchases", "read:inventory", "write:inventory", "adjust:inventory", "read:reports", "read:settings"], "special_permissions": {"can_adjust_inventory": true, "can_manage_warehouses": true, "can_approve_purchases": true, "can_transfer_stock": true, "can_view_cost_reports": true}}'::JSONB,
    4,
    true,
    true,
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
);

-- 6. VENDEDOR_SENIOR - Vendedor Senior
INSERT INTO roles (
    id, code, name, description, role_type, permissions, priority_level, 
    active, is_system_role, created_at, updated_at
) VALUES (
    gen_random_uuid(),
    'VENDEDOR_SENIOR',
    'Vendedor Senior',
    'Vendedor experimentado con permisos de descuentos y acceso a reportes básicos',
    'employee',
    '{"scopes": ["read", "read:products", "read:sales", "write:sales", "pos:sales", "read:inventory", "read:reports"], "special_permissions": {"max_discount_percent": 15, "can_view_own_sales": true, "can_access_pos": true, "can_handle_returns": true}}'::JSONB,
    5,
    true,
    false,
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
);

-- 7. VENDEDOR - Vendedor Básico
INSERT INTO roles (
    id, code, name, description, role_type, permissions, priority_level, 
    active, is_system_role, created_at, updated_at
) VALUES (
    gen_random_uuid(),
    'VENDEDOR',
    'Vendedor',
    'Vendedor básico con acceso al punto de venta y funciones esenciales',
    'employee',
    '{"scopes": ["read", "read:products", "read:sales", "write:sales", "pos:sales", "read:inventory"], "special_permissions": {"max_discount_percent": 5, "can_view_own_sales": true, "can_access_pos": true}}'::JSONB,
    6,
    true,
    false,
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
);

-- 8. CAJERO - Cajero/Operador de Caja
INSERT INTO roles (
    id, code, name, description, role_type, permissions, priority_level, 
    active, is_system_role, created_at, updated_at
) VALUES (
    gen_random_uuid(),
    'CAJERO',
    'Cajero',
    'Operador de caja con acceso limitado al punto de venta',
    'cashier',
    '{"scopes": ["read", "read:products", "pos:sales"], "special_permissions": {"max_discount_percent": 2, "can_access_pos": true, "can_process_payments": true, "requires_supervisor_approval": true}}'::JSONB,
    7,
    true,
    false,
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
);

-- 9. AUDITOR - Auditor del Sistema
INSERT INTO roles (
    id, code, name, description, role_type, permissions, priority_level, 
    active, is_system_role, created_at, updated_at
) VALUES (
    gen_random_uuid(),
    'AUDITOR',
    'Auditor',
    'Acceso de solo lectura para auditoría y revisión de operaciones',
    'auditor',
    '{"scopes": ["read", "read:users", "read:products", "read:sales", "read:purchases", "read:inventory", "read:reports", "advanced:reports", "read:audit", "read:settings"], "special_permissions": {"can_view_all_transactions": true, "can_generate_audit_reports": true, "can_view_user_activity": true, "read_only_access": true}}'::JSONB,
    8,
    true,
    true,
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
);

-- 10. API_EXTERNA - API Externa
INSERT INTO roles (
    id, code, name, description, role_type, permissions, priority_level, 
    active, is_system_role, created_at, updated_at
) VALUES (
    gen_random_uuid(),
    'API_EXTERNA',
    'API Externa',
    'Acceso para integraciones externas y sistemas third-party',
    'api_user',
    '{"scopes": ["read", "read:products", "read:sales", "read:inventory", "read:reports"], "special_permissions": {"api_access_only": true, "rate_limit": "1000/hour", "can_sync_products": true, "can_query_stock": true}}'::JSONB,
    9,
    true,
    true,
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
);

COMMIT;

-- =====================================================
-- CREAR USUARIO ADMINISTRADOR POR DEFECTO
-- =====================================================

BEGIN;

-- Insertar usuario administrador (solo si no existe)
INSERT INTO users (
    id, username, email, full_name, password, active, superuser, role, created_at, updated_at
)
SELECT 
    gen_random_uuid(),
    'admin',
    'admin@empresa.com',
    'Administrador del Sistema',
    '$2b$12$nroa/gRFIV3nvIZgaCFXke8CB8bG2otMNy44YVmnxvyNhPyPlRpqe', -- password: admin123
    true,
    true,
    'ADMIN',
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
WHERE NOT EXISTS (
    SELECT 1 FROM users WHERE email = 'admin@empresa.com'
);

-- Asignar rol SUPERADMIN al usuario administrador
INSERT INTO user_roles (
    id, user_id, role_id, is_primary, active, assigned_at
)
SELECT 
    gen_random_uuid(),
    u.id,
    r.id,
    true,
    true,
    CURRENT_TIMESTAMP
FROM users u
CROSS JOIN roles r
WHERE u.email = 'admin@empresa.com' 
  AND r.code = 'SUPERADMIN'
  AND NOT EXISTS (
      SELECT 1 FROM user_roles ur 
      WHERE ur.user_id = u.id AND ur.role_id = r.id
  );

COMMIT;

-- =====================================================
-- USUARIOS DE EJEMPLO CON DIFERENTES ROLES
-- =====================================================

BEGIN;

-- Gerente General
INSERT INTO users (
    id, username, email, full_name, password, active, superuser, role, created_at, updated_at
)
SELECT 
    gen_random_uuid(),
    'gerente.general',
    'gerente@empresa.com',
    'Juan Carlos Pérez - Gerente General',
    '$2b$12$nroa/gRFIV3nvIZgaCFXke8CB8bG2otMNy44YVmnxvyNhPyPlRpqe', -- password: admin123
    true,
    false,
    'MANAGER',
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
WHERE NOT EXISTS (
    SELECT 1 FROM users WHERE email = 'gerente@empresa.com'
);

-- Asignar rol GERENTE_GENERAL
INSERT INTO user_roles (id, user_id, role_id, is_primary, active, assigned_at)
SELECT gen_random_uuid(), u.id, r.id, true, true, CURRENT_TIMESTAMP
FROM users u CROSS JOIN roles r
WHERE u.email = 'gerente@empresa.com' AND r.code = 'GERENTE_GENERAL'
  AND NOT EXISTS (SELECT 1 FROM user_roles ur WHERE ur.user_id = u.id AND ur.role_id = r.id);

-- Vendedor Senior
INSERT INTO users (
    id, username, email, full_name, password, active, superuser, role, created_at, updated_at
)
SELECT 
    gen_random_uuid(),
    'vendedor.senior',
    'vendedor.senior@empresa.com',
    'María González - Vendedora Senior',
    '$2b$12$nroa/gRFIV3nvIZgaCFXke8CB8bG2otMNy44YVmnxvyNhPyPlRpqe',
    true,
    false,
    'EMPLOYEE',
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
WHERE NOT EXISTS (
    SELECT 1 FROM users WHERE email = 'vendedor.senior@empresa.com'
);

-- Asignar rol VENDEDOR_SENIOR
INSERT INTO user_roles (id, user_id, role_id, is_primary, active, assigned_at)
SELECT gen_random_uuid(), u.id, r.id, true, true, CURRENT_TIMESTAMP
FROM users u CROSS JOIN roles r
WHERE u.email = 'vendedor.senior@empresa.com' AND r.code = 'VENDEDOR_SENIOR'
  AND NOT EXISTS (SELECT 1 FROM user_roles ur WHERE ur.user_id = u.id AND ur.role_id = r.id);

-- Cajero
INSERT INTO users (
    id, username, email, full_name, password, active, superuser, role, created_at, updated_at
)
SELECT 
    gen_random_uuid(),
    'cajero',
    'cajero@empresa.com',
    'Carlos Rodríguez - Cajero',
    '$2b$12$nroa/gRFIV3nvIZgaCFXke8CB8bG2otMNy44YVmnxvyNhPyPlRpqe',
    true,
    false,
    'CASHIER',
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
WHERE NOT EXISTS (
    SELECT 1 FROM users WHERE email = 'cajero@empresa.com'
);

-- Asignar rol CAJERO
INSERT INTO user_roles (id, user_id, role_id, is_primary, active, assigned_at)
SELECT gen_random_uuid(), u.id, r.id, true, true, CURRENT_TIMESTAMP
FROM users u CROSS JOIN roles r
WHERE u.email = 'cajero@empresa.com' AND r.code = 'CAJERO'
  AND NOT EXISTS (SELECT 1 FROM user_roles ur WHERE ur.user_id = u.id AND ur.role_id = r.id);

-- Contador
INSERT INTO users (
    id, username, email, full_name, password, active, superuser, role, created_at, updated_at
)
SELECT 
    gen_random_uuid(),
    'contador',
    'contador@empresa.com',
    'Ana Martínez - Contadora',
    '$2b$12$nroa/gRFIV3nvIZgaCFXke8CB8bG2otMNy44YVmnxvyNhPyPlRpqe',
    true,
    false,
    'EMPLOYEE',
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
WHERE NOT EXISTS (
    SELECT 1 FROM users WHERE email = 'contador@empresa.com'
);

-- Asignar rol CONTADOR
INSERT INTO user_roles (id, user_id, role_id, is_primary, active, assigned_at)
SELECT gen_random_uuid(), u.id, r.id, true, true, CURRENT_TIMESTAMP
FROM users u CROSS JOIN roles r
WHERE u.email = 'contador@empresa.com' AND r.code = 'CONTADOR'
  AND NOT EXISTS (SELECT 1 FROM user_roles ur WHERE ur.user_id = u.id AND ur.role_id = r.id);

-- Jefe de Almacén
INSERT INTO users (
    id, username, email, full_name, password, active, superuser, role, created_at, updated_at
)
SELECT 
    gen_random_uuid(),
    'jefe.almacen',
    'jefe.almacen@empresa.com',
    'Roberto Jiménez - Jefe de Almacén',
    '$2b$12$nroa/gRFIV3nvIZgaCFXke8CB8bG2otMNy44YVmnxvyNhPyPlRpqe',
    true,
    false,
    'EMPLOYEE',
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
WHERE NOT EXISTS (
    SELECT 1 FROM users WHERE email = 'jefe.almacen@empresa.com'
);

-- Asignar rol JEFE_ALMACEN
INSERT INTO user_roles (id, user_id, role_id, is_primary, active, assigned_at)
SELECT gen_random_uuid(), u.id, r.id, true, true, CURRENT_TIMESTAMP
FROM users u CROSS JOIN roles r
WHERE u.email = 'jefe.almacen@empresa.com' AND r.code = 'JEFE_ALMACEN'
  AND NOT EXISTS (SELECT 1 FROM user_roles ur WHERE ur.user_id = u.id AND ur.role_id = r.id);

COMMIT;

-- =====================================================
-- CONSULTAS DE VERIFICACIÓN
-- =====================================================

-- Ver todos los roles creados
SELECT 
    code AS "Código",
    name AS "Nombre",
    role_type AS "Tipo",
    priority_level AS "Prioridad",
    CASE WHEN is_system_role THEN 'Sí' ELSE 'No' END AS "Sistema",
    (permissions->>'scopes')::text AS "Scopes",
    created_at AS "Creado"
FROM roles 
ORDER BY priority_level, code;

-- Ver usuarios con sus roles asignados
SELECT 
    u.email AS "Email",
    u.full_name AS "Nombre Completo",
    u.role AS "Rol Enum",
    r.code AS "Código Rol",
    r.name AS "Nombre Rol",
    CASE WHEN ur.is_primary THEN 'Sí' ELSE 'No' END AS "Principal"
FROM users u
LEFT JOIN user_roles ur ON u.id = ur.user_id AND ur.active = true
LEFT JOIN roles r ON ur.role_id = r.id
ORDER BY u.email;

-- Estadísticas de roles
SELECT 
    'Total Roles' AS "Métrica", 
    COUNT(*)::text AS "Valor" 
FROM roles
UNION ALL
SELECT 
    'Roles Activos' AS "Métrica", 
    COUNT(*)::text AS "Valor" 
FROM roles WHERE active = true
UNION ALL
SELECT 
    'Roles del Sistema' AS "Métrica", 
    COUNT(*)::text AS "Valor" 
FROM roles WHERE is_system_role = true
UNION ALL
SELECT 
    'Total Usuarios' AS "Métrica", 
    COUNT(*)::text AS "Valor" 
FROM users
UNION ALL
SELECT 
    'Asignaciones de Roles' AS "Métrica", 
    COUNT(*)::text AS "Valor" 
FROM user_roles WHERE active = true;

-- Verificar JSON de permisos
SELECT 
    code AS "Rol",
    jsonb_array_length(permissions->'scopes') AS "Cantidad Scopes",
    permissions->'special_permissions'->>'max_discount_percent' AS "% Descuento Máx"
FROM roles
WHERE permissions->'special_permissions'->>'max_discount_percent' IS NOT NULL
ORDER BY (permissions->'special_permissions'->>'max_discount_percent')::int DESC;

-- =====================================================
-- INFORMACIÓN IMPORTANTE
-- =====================================================

/*
🔐 CREDENCIALES CREADAS:

📧 admin@empresa.com           | 🔑 admin123 | 👑 SUPERADMIN
📧 gerente@empresa.com         | 🔑 admin123 | 👔 GERENTE_GENERAL  
📧 vendedor.senior@empresa.com | 🔑 admin123 | 🏆 VENDEDOR_SENIOR
📧 cajero@empresa.com          | 🔑 admin123 | 💰 CAJERO
📧 contador@empresa.com        | 🔑 admin123 | 📊 CONTADOR
📧 jefe.almacen@empresa.com    | 🔑 admin123 | 📦 JEFE_ALMACEN

⚠️  IMPORTANTE: Cambiar todas las contraseñas en producción!

📋 ROLES DISPONIBLES:
1. SUPERADMIN        (Prioridad 1) - Acceso total
2. GERENTE_GENERAL   (Prioridad 2) - Gestión ejecutiva
3. GERENTE_VENTAS    (Prioridad 3) - Gestión comercial
4. CONTADOR          (Prioridad 3) - Gestión contable
5. JEFE_ALMACEN      (Prioridad 4) - Gestión inventarios
6. VENDEDOR_SENIOR   (Prioridad 5) - Ventas avanzadas
7. VENDEDOR          (Prioridad 6) - Ventas básicas
8. CAJERO            (Prioridad 7) - Operación caja
9. AUDITOR           (Prioridad 8) - Solo lectura
10. API_EXTERNA      (Prioridad 9) - Integraciones

🚀 PRÓXIMOS PASOS:
1. Ejecutar este script en tu base de datos PostgreSQL:
   psql -U usuario -d database_name -f insert_roles_postgresql.sql

2. Verificar que los roles se crearon correctamente:
   SELECT code, name FROM roles ORDER BY priority_level;

3. Cambiar contraseñas por defecto:
   UPDATE users SET password = '$nuevo_hash' WHERE email = 'admin@empresa.com';

4. Crear usuarios adicionales según necesidad
5. Configurar OAuth2 clients para cada tipo de usuario

💡 FUNCIONES POSTGRESQL UTILIZADAS:
- gen_random_uuid() - Genera UUIDs únicos
- CURRENT_TIMESTAMP - Timestamp actual con zona horaria
- ::JSONB - Cast explícito a tipo JSONB para mejor rendimiento
- NOT EXISTS - Evita duplicados en re-ejecuciones del script

🔧 CARACTERÍSTICAS ESPECÍFICAS POSTGRESQL:
- Extensiones uuid-ossp y pgcrypto habilitadas
- Uso de JSONB para mejor rendimiento en consultas JSON
- Transacciones explícitas con BEGIN/COMMIT
- Consultas de verificación incluidas
- Manejo de duplicados con NOT EXISTS
*/
