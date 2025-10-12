from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Base de datos
    DATABASE_URL: str = "sqlite:///./imss_pension.db"
    
    # JWT
    SECRET_KEY: str = "tu-super-secret-key-cambiala-en-produccion-12345"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080  # 7 días
    
    # App
    APP_NAME: str = "IMSS Pension Analyzer"
    APP_VERSION: str = "3.0.0"
    DEBUG: bool = True
    
    # Google Sheets (opcional, para después)
    GOOGLE_SHEETS_CREDENTIALS: Optional[str] = None
    SPREADSHEET_ID: Optional[str] = None
    
    class Config:
        env_file = ".env"
        extra = "allow"  # Permitir variables extra sin error

settings = Settings()


