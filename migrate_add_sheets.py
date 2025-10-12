from sqlalchemy import create_engine, text
from src.api.config import settings

def migrate():
    engine = create_engine(settings.DATABASE_URL)
    
    with engine.connect() as conn:
        try:
            # Agregar columnas nuevas
            conn.execute(text("ALTER TABLE users ADD COLUMN company_name VARCHAR"))
            print("✅ Columna company_name agregada")
        except Exception as e:
            print(f"⚠️  company_name ya existe o error: {e}")
        
        try:
            conn.execute(text("ALTER TABLE users ADD COLUMN spreadsheet_id VARCHAR"))
            print("✅ Columna spreadsheet_id agregada")
        except Exception as e:
            print(f"⚠️  spreadsheet_id ya existe o error: {e}")
        
        try:
            conn.execute(text("ALTER TABLE users ADD COLUMN spreadsheet_url VARCHAR"))
            print("✅ Columna spreadsheet_url agregada")
        except Exception as e:
            print(f"⚠️  spreadsheet_url ya existe o error: {e}")
        
        try:
            conn.execute(text("ALTER TABLE users ADD COLUMN sheet_created_at TIMESTAMP"))
            print("✅ Columna sheet_created_at agregada")
        except Exception as e:
            print(f"⚠️  sheet_created_at ya existe o error: {e}")
        
        conn.commit()
    
    print("\n✅ Migración completada")

if __name__ == "__main__":
    migrate()


