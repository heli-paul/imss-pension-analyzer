"""
Migración para agregar créditos a invitations.
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
        print("🔄 Aplicando migración de créditos a invitations...")
        
        queries = [
            "ALTER TABLE invitations ADD COLUMN IF NOT EXISTS initial_credits INTEGER DEFAULT 10 NOT NULL",
            "ALTER TABLE invitations ADD COLUMN IF NOT EXISTS credits_valid_days INTEGER DEFAULT 30 NOT NULL"
        ]
        
        for query in queries:
            try:
                conn.execute(text(query))
                conn.commit()
                print(f"✅ Ejecutado: {query[:60]}...")
            except Exception as e:
                print(f"⚠️ Error (puede ser que ya exista): {e}")
        
        print("✅ Migración completada")

if __name__ == "__main__":
    migrate()
