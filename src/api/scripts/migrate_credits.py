"""
Migración para agregar sistema de créditos.
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from sqlalchemy import create_engine, text
from api.config import get_settings

def migrate():
    settings = get_settings()
    engine = create_engine(settings.DATABASE_URL)
    
    with engine.connect() as conn:
        print("🔄 Aplicando migración de créditos...")
        
        # Agregar columnas si no existen
        queries = [
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS credits INTEGER DEFAULT 10 NOT NULL",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS credits_expire_at TIMESTAMP",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS company_size VARCHAR(20)"
        ]
        
        for query in queries:
            try:
                conn.execute(text(query))
                conn.commit()
                print(f"✅ Ejecutado: {query[:50]}...")
            except Exception as e:
                print(f"⚠️ Error (puede ser que ya exista): {e}")
        
        print("✅ Migración completada")

if __name__ == "__main__":
    migrate()
