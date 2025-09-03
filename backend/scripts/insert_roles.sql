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
    uuid_generate_v4(),
    'SUPERADMIN',
    'Super Administrador',
    'Acceso completo al sistema, puede gestionar todo incluyendo configuraciones críticas',
    'admin'::VARCHAR,
    '{
        "scopes": [
            "admin", "read", "write", "delete",
            "read:users", "write:users", "delete:users",
            "read:products", "write:products", "delete:products",
            "read:sales", "write:sales", "delete:sales", "pos:sales",
            "read:purchases", "write:purchases", "delete:purchases",
            "read:inventory", "write:inventory", "adjust:inventory",
            "read:reports", "advanced:reports", "export:reports",
            "read:settings", "write:settings",
            "read:audit", "write:audit",
            "manage:system", "backup:system",
            "read:roles", "write:roles", "assign:roles"
        ],
        "special_permissions": {
            "can_delete_transactions": true,
            "can_modify_prices": true,
            "can_access_all_warehouses": true,
            "can_override_discounts": true,
            "max_discount_percent": 100
        }
    }'::JSONB,
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
    uuid_generate_v4(),
    'GERENTE_GENERAL',
    'Gerente General',
    'Gestión completa del negocio, reportes ejecutivos y supervisión de operaciones',
    'manager'::VARCHAR,
    '{
        "scopes": [
            "read", "write",
            "read:users", "write:users",
            "read:products", "write:products",
            "read:sales", "write:sales", "pos:sales",
            "read:purchases", "write:purchases",
            "read:inventory", "write:inventory",
            "read:reports", "advanced:reports", "export:reports",
            "read:settings",
            "read:audit",
            "read:roles", "assign:roles"
        ],
        "special_permissions": {
            "can_modify_prices": true,
            "can_access_all_warehouses": true,
            "can_override_discounts": true,
            "max_discount_percent": 50,
            "can_view_financial_reports": true
        }
    }'::JSONB,
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
    '{
        "scopes": [
            "read", "write",
            "read:users",
            "read:products", "write:products",
            "read:sales", "write:sales", "pos:sales",
            "read:inventory",
            "read:reports", "advanced:reports",
            "read:settings"
        ],
        "special_permissions": {
            "can_modify_prices": true,
            "can_manage_sales_team": true,
            "can_set_sales_targets": true,
            "max_discount_percent": 30,
            "can_view_sales_reports": true
        }
    }',
    3,
    true,
    true,
    NOW(),
    NOW()
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
    '{
        "scopes": [
            "read",
            "read:users",
            "read:products",
            "read:sales",
            "read:purchases", "write:purchases",
            "read:inventory",
            "read:reports", "advanced:reports", "export:reports",
            "read:audit"
        ],
        "special_permissions": {
            "can_view_financial_reports": true,
            "can_manage_accounts": true,
            "can_generate_tax_reports": true,
            "can_view_all_transactions": true
        }
    }',
    3,
    true,
    true,
    NOW(),
    NOW()
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
    '{
        "scopes": [
            "read", "write",
            "read:products", "write:products",
            "read:purchases", "write:purchases",
            "read:inventory", "write:inventory", "adjust:inventory",
            "read:reports",
            "read:settings"
        ],
        "special_permissions": {
            "can_adjust_inventory": true,
            "can_manage_warehouses": true,
            "can_approve_purchases": true,
            "can_transfer_stock": true,
            "can_view_cost_reports": true
        }
    }',
    4,
    true,
    true,
    NOW(),
    NOW()
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
    '{
        "scopes": [
            "read",
            "read:products",
            "read:sales", "write:sales", "pos:sales",
            "read:inventory",
            "read:reports"
        ],
        "special_permissions": {
            "max_discount_percent": 15,
            "can_view_own_sales": true,
            "can_access_pos": true,
            "can_handle_returns": true
        }
    }',
    5,
    true,
    false,
    NOW(),
    NOW()
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
    '{
        "scopes": [
            "read",
            "read:products",
            "read:sales", "write:sales", "pos:sales",
            "read:inventory"
        ],
        "special_permissions": {
            "max_discount_percent": 5,
            "can_view_own_sales": true,
            "can_access_pos": true
        }
    }',
    6,
    true,
    false,
    NOW(),
    NOW()
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
    '{
        "scopes": [
            "read",
            "read:products",
            "pos:sales"
        ],
        "special_permissions": {
            "max_discount_percent": 2,
            "can_access_pos": true,
            "can_process_payments": true,
            "requires_supervisor_approval": true
        }
    }',
    7,
    true,
    false,
    NOW(),
    NOW()
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
    '{
        "scopes": [
            "read",
            "read:users",
            "read:products",
            "read:sales",
            "read:purchases",
            "read:inventory",
            "read:reports", "advanced:reports",
            "read:audit",
            "read:settings"
        ],
        "special_permissions": {
            "can_view_all_transactions": true,
            "can_generate_audit_reports": true,
            "can_view_user_activity": true,
            "read_only_access": true
        }
    }',
    8,
    true,
    true,
    NOW(),
    NOW()
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
    '{
        "scopes": [
            "read",
            "read:products",
            "read:sales",
            "read:inventory",
            "read:reports"
        ],
        "special_permissions": {
            "api_access_only": true,
            "rate_limit": "1000/hour",
            "can_sync_products": true,
            "can_query_stock": true
        }
    }',
    9,
    true,
    true,
    NOW(),
    NOW()
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
    NOW(),
    NOW()
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
    NOW()
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
    NOW(),
    NOW()
WHERE NOT EXISTS (
    SELECT 1 FROM users WHERE email = 'gerente@empresa.com'
);

-- Asignar rol
INSERT INTO user_roles (id, user_id, role_id, is_primary, active, assigned_at)
SELECT gen_random_uuid(), u.id, r.id, true, true, NOW()
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
    NOW(),
    NOW()
WHERE NOT EXISTS (
    SELECT 1 FROM users WHERE email = 'vendedor.senior@empresa.com'
);

-- Asignar rol
INSERT INTO user_roles (id, user_id, role_id, is_primary, active, assigned_at)
SELECT gen_random_uuid(), u.id, r.id, true, true, NOW()
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
    NOW(),
    NOW()
WHERE NOT EXISTS (
    SELECT 1 FROM users WHERE email = 'cajero@empresa.com'
);

-- Asignar rol
INSERT INTO user_roles (id, user_id, role_id, is_primary, active, assigned_at)
SELECT gen_random_uuid(), u.id, r.id, true, true, NOW()
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
    NOW(),
    NOW()
WHERE NOT EXISTS (
    SELECT 1 FROM users WHERE email = 'contador@empresa.com'
);

-- Asignar rol
INSERT INTO user_roles (id, user_id, role_id, is_primary, active, assigned_at)
SELECT gen_random_uuid(), u.id, r.id, true, true, NOW()
FROM users u CROSS JOIN roles r
WHERE u.email = 'contador@empresa.com' AND r.code = 'CONTADOR'
  AND NOT EXISTS (SELECT 1 FROM user_roles ur WHERE ur.user_id = u.id AND ur.role_id = r.id);

COMMIT;

-- =====================================================
-- CONSULTAS DE VERIFICACIÓN
-- =====================================================

-- Ver todos los roles creados
SELECT 
    code,
    name,
    role_type,
    priority_level,
    is_system_role,
    (permissions->>'scopes')::jsonb as scopes,
    created_at
FROM roles 
ORDER BY priority_level, code;

-- Ver usuarios con sus roles asignados
SELECT 
    u.email,
    u.full_name,
    u.role as user_enum_role,
    r.code as assigned_role_code,
    r.name as assigned_role_name,
    ur.is_primary
FROM users u
LEFT JOIN user_roles ur ON u.id = ur.user_id AND ur.active = true
LEFT JOIN roles r ON ur.role_id = r.id
ORDER BY u.email;

-- Estadísticas de roles
SELECT 
    'Total Roles' as metric, 
    COUNT(*)::text as value 
FROM roles
UNION ALL
SELECT 
    'Roles Activos' as metric, 
    COUNT(*)::text as value 
FROM roles WHERE active = true
UNION ALL
SELECT 
    'Roles del Sistema' as metric, 
    COUNT(*)::text as value 
FROM roles WHERE is_system_role = true
UNION ALL
SELECT 
    'Total Usuarios' as metric, 
    COUNT(*)::text as value 
FROM users
UNION ALL
SELECT 
    'Asignaciones de Roles' as metric, 
    COUNT(*)::text as value 
FROM user_roles WHERE active = true;

-- =====================================================
-- INFORMACIÓN IMPORTANTE
-- =====================================================

/*
🔐 CREDENCIALES CREADAS:

📧 admin@empresa.com          | 🔑 admin123      | 👑 SUPERADMIN
📧 gerente@empresa.com        | 🔑 admin123      | 👔 GERENTE_GENERAL  
📧 vendedor.senior@empresa.com| 🔑 admin123      | 🏆 VENDEDOR_SENIOR
📧 cajero@empresa.com         | 🔑 admin123      | 💰 CAJERO
📧 contador@empresa.com       | 🔑 admin123      | 📊 CONTADOR

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
1. Ejecutar este script en tu base de datos PostgreSQL
2. Verificar que los roles se crearon correctamente
3. Cambiar contraseñas por defecto
4. Crear usuarios adicionales según necesidad
5. Configurar OAuth2 clients para cada tipo de usuario
*/
