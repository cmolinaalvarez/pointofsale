#!/usr/bin/env python3
"""
Script para insertar 10 perfiles/roles profesionales en el sistema de ventas

Este script crea roles predefinidos con permisos específicos para diferentes
tipos de usuarios en un sistema de punto de venta y gestión empresarial.

Ejecutar: python insert_default_roles.py
"""

import asyncio
import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
import uuid
import json

# Agregar el directorio raíz al path
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import async_session_factory
from app.models.role import Role, RoleType, UserRole
from app.models.user import User

# ======================
# DEFINICIÓN DE 10 PERFILES PROFESIONALES
# ======================

DEFAULT_ROLES = [
    {
        "code": "SUPERADMIN",
        "name": "Super Administrador",
        "description": "Acceso completo al sistema, puede gestionar todo incluyendo configuraciones críticas",
        "role_type": RoleType.ADMIN,
        "priority_level": 1,
        "is_system_role": True,
        "permissions": {
            "scopes": [
                "admin",
                "read", "write", "delete",
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
                "can_delete_transactions": True,
                "can_modify_prices": True,
                "can_access_all_warehouses": True,
                "can_override_discounts": True,
                "max_discount_percent": 100
            }
        }
    },
    {
        "code": "GERENTE_GENERAL",
        "name": "Gerente General",
        "description": "Gestión completa del negocio, reportes ejecutivos y supervisión de operaciones",
        "role_type": RoleType.MANAGER,
        "priority_level": 2,
        "is_system_role": True,
        "permissions": {
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
                "can_modify_prices": True,
                "can_access_all_warehouses": True,
                "can_override_discounts": True,
                "max_discount_percent": 50,
                "can_view_financial_reports": True
            }
        }
    },
    {
        "code": "GERENTE_VENTAS",
        "name": "Gerente de Ventas",
        "description": "Gestión del equipo de ventas, metas, comisiones y reportes comerciales",
        "role_type": RoleType.MANAGER,
        "priority_level": 3,
        "is_system_role": True,
        "permissions": {
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
                "can_modify_prices": True,
                "can_manage_sales_team": True,
                "can_set_sales_targets": True,
                "max_discount_percent": 30,
                "can_view_sales_reports": True
            }
        }
    },
    {
        "code": "CONTADOR",
        "name": "Contador/Contabilidad",
        "description": "Gestión contable, reportes financieros, cuentas por pagar y cobrar",
        "role_type": RoleType.EMPLOYEE,
        "priority_level": 3,
        "is_system_role": True,
        "permissions": {
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
                "can_view_financial_reports": True,
                "can_manage_accounts": True,
                "can_generate_tax_reports": True,
                "can_view_all_transactions": True
            }
        }
    },
    {
        "code": "JEFE_ALMACEN",
        "name": "Jefe de Almacén",
        "description": "Gestión completa de inventarios, compras, stocks y almacenes",
        "role_type": RoleType.SUPERVISOR,
        "priority_level": 4,
        "is_system_role": True,
        "permissions": {
            "scopes": [
                "read", "write",
                "read:products", "write:products",
                "read:purchases", "write:purchases",
                "read:inventory", "write:inventory", "adjust:inventory",
                "read:reports",
                "read:settings"
            ],
            "special_permissions": {
                "can_adjust_inventory": True,
                "can_manage_warehouses": True,
                "can_approve_purchases": True,
                "can_transfer_stock": True,
                "can_view_cost_reports": True
            }
        }
    },
    {
        "code": "VENDEDOR_SENIOR",
        "name": "Vendedor Senior",
        "description": "Vendedor experimentado con permisos de descuentos y acceso a reportes básicos",
        "role_type": RoleType.EMPLOYEE,
        "priority_level": 5,
        "is_system_role": False,
        "permissions": {
            "scopes": [
                "read",
                "read:products",
                "read:sales", "write:sales", "pos:sales",
                "read:inventory",
                "read:reports"
            ],
            "special_permissions": {
                "max_discount_percent": 15,
                "can_view_own_sales": True,
                "can_access_pos": True,
                "can_handle_returns": True
            }
        }
    },
    {
        "code": "VENDEDOR",
        "name": "Vendedor",
        "description": "Vendedor básico con acceso al punto de venta y funciones esenciales",
        "role_type": RoleType.EMPLOYEE,
        "priority_level": 6,
        "is_system_role": False,
        "permissions": {
            "scopes": [
                "read",
                "read:products",
                "read:sales", "write:sales", "pos:sales",
                "read:inventory"
            ],
            "special_permissions": {
                "max_discount_percent": 5,
                "can_view_own_sales": True,
                "can_access_pos": True
            }
        }
    },
    {
        "code": "CAJERO",
        "name": "Cajero",
        "description": "Operador de caja con acceso limitado al punto de venta",
        "role_type": RoleType.CASHIER,
        "priority_level": 7,
        "is_system_role": False,
        "permissions": {
            "scopes": [
                "read",
                "read:products",
                "pos:sales"
            ],
            "special_permissions": {
                "max_discount_percent": 2,
                "can_access_pos": True,
                "can_process_payments": True,
                "requires_supervisor_approval": True
            }
        }
    },
    {
        "code": "AUDITOR",
        "name": "Auditor",
        "description": "Acceso de solo lectura para auditoría y revisión de operaciones",
        "role_type": RoleType.AUDITOR,
        "priority_level": 8,
        "is_system_role": True,
        "permissions": {
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
                "can_view_all_transactions": True,
                "can_generate_audit_reports": True,
                "can_view_user_activity": True,
                "read_only_access": True
            }
        }
    },
    {
        "code": "API_EXTERNA",
        "name": "API Externa",
        "description": "Acceso para integraciones externas y sistemas third-party",
        "role_type": RoleType.API_USER,
        "priority_level": 9,
        "is_system_role": True,
        "permissions": {
            "scopes": [
                "read",
                "read:products",
                "read:sales",
                "read:inventory",
                "read:reports"
            ],
            "special_permissions": {
                "api_access_only": True,
                "rate_limit": "1000/hour",
                "can_sync_products": True,
                "can_query_stock": True
            }
        }
    }
]

# ======================
# FUNCIONES DE INSERCIÓN
# ======================

async def insert_default_roles():
    """Insertar los roles por defecto en la base de datos"""
    
    print("🚀 Iniciando inserción de roles por defecto...")
    
    async with async_session_factory() as session:
        try:
            # Verificar si ya existen roles
            existing_roles = await session.execute(
                "SELECT COUNT(*) FROM roles"
            )
            count = existing_roles.scalar()
            
            if count > 0:
                print(f"⚠️  Ya existen {count} roles en el sistema.")
                response = input("¿Deseas continuar y agregar los roles faltantes? (s/n): ")
                if response.lower() != 's':
                    print("❌ Operación cancelada.")
                    return
            
            inserted_count = 0
            skipped_count = 0
            
            for role_data in DEFAULT_ROLES:
                # Verificar si el rol ya existe
                existing_role = await session.execute(
                    f"SELECT id FROM roles WHERE code = '{role_data['code']}'"
                )
                
                if existing_role.scalar():
                    print(f"⏭️  Rol '{role_data['code']}' ya existe, omitiendo...")
                    skipped_count += 1
                    continue
                
                # Crear el rol
                role = Role(
                    id=uuid.uuid4(),
                    code=role_data["code"],
                    name=role_data["name"],
                    description=role_data["description"],
                    role_type=role_data["role_type"],
                    permissions=role_data["permissions"],
                    priority_level=role_data["priority_level"],
                    is_system_role=role_data["is_system_role"],
                    active=True,
                    created_at=datetime.utcnow()
                )
                
                session.add(role)
                print(f"✅ Creando rol: {role_data['name']} ({role_data['code']})")
                inserted_count += 1
            
            # Confirmar cambios
            await session.commit()
            
            print(f"\n🎉 ¡Proceso completado!")
            print(f"📊 Roles insertados: {inserted_count}")
            print(f"📊 Roles omitidos: {skipped_count}")
            print(f"📊 Total en sistema: {inserted_count + skipped_count}")
            
        except Exception as e:
            await session.rollback()
            print(f"❌ Error al insertar roles: {str(e)}")
            raise

async def create_admin_user_with_role():
    """Crear un usuario administrador por defecto con rol asignado"""
    
    print("\n👤 Creando usuario administrador por defecto...")
    
    async with async_session_factory() as session:
        try:
            # Verificar si ya existe un superadmin
            existing_admin = await session.execute(
                "SELECT id FROM users WHERE email = 'admin@empresa.com'"
            )
            
            if existing_admin.scalar():
                print("⚠️  Usuario administrador ya existe.")
                return
            
            # Obtener el rol de SUPERADMIN
            superadmin_role = await session.execute(
                "SELECT id FROM roles WHERE code = 'SUPERADMIN'"
            )
            role_id = superadmin_role.scalar()
            
            if not role_id:
                print("❌ Rol SUPERADMIN no encontrado. Ejecuta primero la inserción de roles.")
                return
            
            # Crear usuario admin
            from app.utils.security import get_password_hash
            
            admin_user = User(
                id=uuid.uuid4(),
                username="admin",
                email="admin@empresa.com",
                full_name="Administrador del Sistema",
                password=get_password_hash("admin123"),  # Cambiar en producción
                active=True,
                superuser=True,
                role=UserRoleEnum.ADMIN,  # Rol enum del usuario
                created_at=datetime.utcnow()
            )
            
            session.add(admin_user)
            await session.flush()  # Para obtener el ID
            
            # Asignar rol de SUPERADMIN
            user_role_assignment = UserRole(
                id=uuid.uuid4(),
                user_id=admin_user.id,
                role_id=role_id,
                is_primary=True,
                active=True,
                assigned_at=datetime.utcnow()
            )
            
            session.add(user_role_assignment)
            await session.commit()
            
            print("✅ Usuario administrador creado exitosamente")
            print("📧 Email: admin@empresa.com")
            print("🔑 Password: admin123")
            print("⚠️  IMPORTANTE: Cambiar la contraseña en producción!")
            
        except Exception as e:
            await session.rollback()
            print(f"❌ Error al crear usuario administrador: {str(e)}")
            raise

async def display_roles_summary():
    """Mostrar resumen de roles creados"""
    
    print("\n📋 RESUMEN DE ROLES CREADOS:")
    print("=" * 60)
    
    async with async_session_factory() as session:
        try:
            roles = await session.execute(
                """
                SELECT code, name, role_type, priority_level, is_system_role
                FROM roles 
                ORDER BY priority_level, code
                """
            )
            
            for role in roles.fetchall():
                system_mark = "🔒" if role.is_system_role else "👤"
                priority_stars = "⭐" * (6 - role.priority_level) if role.priority_level <= 5 else "📝"
                
                print(f"{system_mark} {priority_stars} {role.code:<15} | {role.name:<25} | {role.role_type}")
            
            print("=" * 60)
            print("🔒 = Rol del Sistema | 👤 = Rol Personalizable")
            print("⭐ = Nivel de Prioridad | 📝 = Rol Operativo")
            
        except Exception as e:
            print(f"❌ Error al mostrar resumen: {str(e)}")

# ======================
# SCRIPT PRINCIPAL
# ======================

async def main():
    """Función principal del script"""
    
    print("🎯 SCRIPT DE INICIALIZACIÓN DE ROLES")
    print("=" * 50)
    print("Este script creará 10 perfiles profesionales para tu sistema de ventas")
    print()
    
    try:
        # 1. Insertar roles por defecto
        await insert_default_roles()
        
        # 2. Crear usuario administrador
        await create_admin_user_with_role()
        
        # 3. Mostrar resumen
        await display_roles_summary()
        
        print("\n🎉 ¡Script ejecutado exitosamente!")
        print("\n🚀 Próximos pasos:")
        print("1. Cambiar la contraseña del administrador")
        print("2. Crear usuarios adicionales y asignar roles")
        print("3. Configurar permisos específicos por contexto")
        print("4. Revisar y ajustar scopes según necesidades")
        
    except Exception as e:
        print(f"\n💥 Error crítico: {str(e)}")
        print("🔧 Verifica la conexión a la base de datos y que las migraciones estén aplicadas")
        return 1
    
    return 0

if __name__ == "__main__":
    """Ejecutar el script"""
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

# ======================
# DOCUMENTACIÓN DE PERFILES
# ======================

"""
📚 DOCUMENTACIÓN DE LOS 10 PERFILES CREADOS:

1. 🔥 SUPERADMIN (Prioridad 1)
   - Acceso completo al sistema
   - Puede modificar cualquier configuración
   - Gestión de usuarios y roles

2. 👔 GERENTE_GENERAL (Prioridad 2)  
   - Gestión ejecutiva completa
   - Reportes financieros
   - Supervisión de operaciones

3. 💼 GERENTE_VENTAS (Prioridad 3)
   - Gestión del equipo comercial
   - Metas y comisiones
   - Reportes de ventas

4. 📊 CONTADOR (Prioridad 3)
   - Gestión contable y financiera
   - Reportes fiscales
   - Auditoría de transacciones

5. 📦 JEFE_ALMACEN (Prioridad 4)
   - Gestión completa de inventarios
   - Compras y ajustes de stock
   - Control de almacenes

6. 🏆 VENDEDOR_SENIOR (Prioridad 5)
   - Ventas con descuentos extendidos
   - Acceso a reportes básicos
   - Manejo de devoluciones

7. 🛒 VENDEDOR (Prioridad 6)
   - Punto de venta básico
   - Descuentos limitados
   - Consulta de productos

8. 💰 CAJERO (Prioridad 7)
   - Operación de caja
   - Procesamiento de pagos
   - Acceso muy limitado

9. 🔍 AUDITOR (Prioridad 8)
   - Solo lectura total
   - Reportes de auditoría
   - Revisión de operaciones

10. 🔌 API_EXTERNA (Prioridad 9)
    - Integraciones third-party
    - Acceso programático
    - Consultas de stock/productos

ESTRUCTURA DE PERMISOS:
- Cada rol tiene scopes específicos definidos
- Permisos especiales según función
- Niveles de descuento diferenciados
- Acceso contextual por almacén/sucursal
"""
