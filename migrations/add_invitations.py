"""
Migration script para agregar el sistema de invitaciones.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, text, inspect
from src.api.config import get_settings
from src.api.database import Base
from src.api.models.user import User
from src.api.models.invitation import Invitation


def check_column_exists(inspector, table_name: str, column_name: str) -> bool:
    """Verifica si una columna existe en una tabla."""
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    return column_name in columns


def check_table_exists(inspector, table_name: str) -> bool:
    """Verifica si una tabla existe."""
    return table_name in inspector.get_table_names()


def run_migration():
    """Ejecuta la migración del sistema de invitaciones."""
    settings = get_settings()
    engine = create_engine(settings.DATABASE_URL)
    inspector = inspect(engine)
    
    print("🚀 Iniciando migración del sistema de invitaciones...")
    print(f"📊 Base de datos: {settings.DATABASE_URL}")
    
    with engine.begin() as conn:
        
        # 1. Crear tabla invitations
        if not check_table_exists(inspector, 'invitations'):
            print("\n📝 Creando tabla 'invitations'...")
            conn.execute(text("""
                CREATE TABLE invitations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email VARCHAR(255) UNIQUE NOT NULL,
                    token VARCHAR(64) UNIQUE NOT NULL,
                    status VARCHAR(20) DEFAULT 'pending' NOT NULL,
                    plan VARCHAR(20) DEFAULT 'free' NOT NULL,
                    cuota_analisis INTEGER DEFAULT 30 NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
                    expires_at TIMESTAMP NOT NULL,
                    used_at TIMESTAMP NULL,
                    user_id INTEGER NULL REFERENCES users(id),
                    created_by INTEGER NOT NULL REFERENCES users(id),
                    notes TEXT
                )
            """))
            
            print("   📌 Creando índices...")
            conn.execute(text("CREATE INDEX idx_invitation_token ON invitations(token)"))
            conn.execute(text("CREATE INDEX idx_invitation_status ON invitations(status)"))
            conn.execute(text("CREATE INDEX idx_invitation_email ON invitations(email)"))
            
            print("   ✅ Tabla 'invitations' creada exitosamente")
        else:
            print("\n⏭️  Tabla 'invitations' ya existe")
        
        # 2. Actualizar tabla users
        print("\n📝 Actualizando tabla 'users'...")
        
        inspector = inspect(engine)
        
        if not check_column_exists(inspector, 'users', 'invited_by'):
            print("   ➕ Agregando columna 'invited_by'...")
            conn.execute(text("ALTER TABLE users ADD COLUMN invited_by INTEGER REFERENCES users(id)"))
            print("   ✅ Columna 'invited_by' agregada")
        else:
            print("   ⏭️  Columna 'invited_by' ya existe")
        
        if not check_column_exists(inspector, 'users', 'invitation_token'):
            print("   ➕ Agregando columna 'invitation_token'...")
            conn.execute(text("ALTER TABLE users ADD COLUMN invitation_token VARCHAR(64)"))
            print("   ✅ Columna 'invitation_token' agregada")
        else:
            print("   ⏭️  Columna 'invitation_token' ya existe")
        
        if not check_column_exists(inspector, 'users', 'is_admin'):
            print("   ➕ Agregando columna 'is_admin'...")
            conn.execute(text("ALTER TABLE users ADD COLUMN is_admin BOOLEAN DEFAULT 0 NOT NULL"))
            print("   ✅ Columna 'is_admin' agregada")
            
            print("   👑 Marcando usuarios admin...")
            conn.execute(text("""
                UPDATE users 
                SET is_admin = 1 
                WHERE email IN ('info@todopension.com', 'heli_paul@todopension.com', 'contacto@pensionasoft.com')
            """))
            print("   ✅ Admins marcados")
        else:
            print("   ⏭️  Columna 'is_admin' ya existe")
    
    print("\n✨ Migración completada exitosamente!")
    print("\n📋 Resumen:")
    print("   • Tabla 'invitations' creada")
    print("   • Columnas agregadas a 'users'")
    print("   • Índices creados")
    print("\n🎯 Sistema de invitaciones listo para usar")


if __name__ == "__main__":
    try:
        run_migration()
    except Exception as e:
        print(f"\n❌ Error en migración: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)



