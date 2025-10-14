"""
Script para inicializar la base de datos en Railway.
"""
import sys
from sqlalchemy import create_engine, text, inspect

# Importar modelos para crear tablas
from src.api.database import Base
from src.api.models.user import User
from src.api.models.invitation import Invitation
from src.api.config import get_settings

def setup_database():
    """Configura la base de datos en Railway."""
    settings = get_settings()
    
    print("🚀 Configurando base de datos en Railway...")
    print(f"📊 DATABASE_URL: {settings.DATABASE_URL[:50]}...")
    
    engine = create_engine(settings.DATABASE_URL)
    
    # Crear todas las tablas
    print("\n📝 Creando tablas...")
    Base.metadata.create_all(bind=engine)
    print("✅ Tablas creadas")
    
    # Verificar tablas creadas
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    print(f"\n📋 Tablas en la base de datos: {tables}")
    
    print("\n✨ Base de datos configurada exitosamente!")

if __name__ == "__main__":
    try:
        setup_database()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


