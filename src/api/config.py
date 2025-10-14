"""
Configuración de la aplicación con soporte de SendGrid.
"""

from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import List


class Settings(BaseSettings):
    """
    Configuración de la aplicación usando variables de entorno.
    """
    
    # Seguridad
    SECRET_KEY: str
    JWT_SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7
    
    # Base de datos
    DATABASE_URL: str
    
    # SendGrid (Email)
    SENDGRID_API_KEY: str = ""
    SENDGRID_FROM_EMAIL: str = "contacto@pensionasoft.com"
    SENDGRID_FROM_NAME: str = "Pensionasoft"
    
    # URLs
    FRONTEND_URL: str = "http://localhost:3000"
    BACKEND_URL: str = "http://localhost:8001"
    
    # Google Sheets (opcional)
    GOOGLE_CREDENTIALS_JSON: str = ""
    SPREADSHEET_ID: str = ""
    
    # Configuración de la app
    APP_NAME: str = "IMSS Pension Analyzer"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """
    Obtiene la configuración de la aplicación (cached).
    """
    return Settings()



