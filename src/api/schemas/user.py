"""
Pydantic schemas actualizados para usuarios con soporte de invitaciones.
"""

from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional
from datetime import datetime


class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None


class UserCreate(UserBase):
    """
    Schema base para crear usuario (usado internamente).
    """
    password: str = Field(..., min_length=8)
    company_name: Optional[str] = None
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError('La contraseña debe tener al menos 8 caracteres')
        return v


class UserRegister(UserCreate):
    """
    Schema para registro público con token de invitación.
    """
    invitation_token: str = Field(..., min_length=10, description="Token de invitación válido")


class UserLogin(BaseModel):
    """
    Schema para login.
    """
    email: EmailStr
    password: str


class UserResponse(UserBase):
    """
    Schema para respuestas de API con información de usuario.
    """
    id: int
    company_name: Optional[str] = None
    is_active: bool
    is_admin: bool
    created_at: datetime
    plan: str
    analisis_realizados: int
    cuota_analisis: int
    # can_analyze: bool
    
    # Google Sheets
    spreadsheet_id: Optional[str] = None
    spreadsheet_url: Optional[str] = None
    sheet_created_at: Optional[datetime] = None
    
    # Sistema de invitaciones
    invited_by: Optional[int] = None
    invitation_token: Optional[str] = None
    
    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    """
    Schema para actualizar información de usuario.
    """
    full_name: Optional[str] = Field(None, min_length=2, max_length=100)
    company_name: Optional[str] = None


class UserChangePassword(BaseModel):
    """
    Schema para cambio de contraseña.
    """
    old_password: str = Field(..., description="Contraseña actual")
    new_password: str = Field(..., min_length=8, description="Nueva contraseña")
    
    @field_validator('new_password')
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError('La contraseña debe tener al menos 8 caracteres')
        return v


class Token(BaseModel):
    """
    Schema para respuesta de autenticación con JWT.
    """
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class UserStatsResponse(BaseModel):
    """
    Schema para estadísticas de uso del usuario.
    """
    analisis_realizados: int
    cuota_analisis: int
    analisis_restantes: int
    porcentaje_usado: float
    plan: str
    puede_analizar: bool



