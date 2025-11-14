"""
Pydantic schemas actualizados para usuarios con soporte de invitaciones y créditos.
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
    company_size: Optional[str] = None  # NUEVO
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError('La contraseña debe tener al menos 8 caracteres')
        return v
    
    @field_validator('company_size')
    @classmethod
    def validate_company_size(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            valid_sizes = ['1-5', '5-10', '10-30', '30-50', '50-100', '100+']
            if v not in valid_sizes:
                raise ValueError(f'Tamaño de empresa debe ser uno de: {", ".join(valid_sizes)}')
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
    company_size: Optional[str] = None  # NUEVO
    is_active: bool
    is_admin: bool
    created_at: datetime
    
    # Sistema legacy (mantenemos por compatibilidad)
    plan: str
    analisis_realizados: int
    cuota_analisis: int
    
    # NUEVO: Sistema de créditos
    credits: int
    credits_expire_at: Optional[datetime] = None
    has_valid_credits: bool = False
    
    # Google Sheets
    spreadsheet_id: Optional[str] = None
    spreadsheet_url: Optional[str] = None
    
    # Sistema de invitaciones
    invited_by: Optional[int] = None
    
    class Config:
        from_attributes = True

class UserUpdate(BaseModel):
    """
    Schema para actualizar información de usuario.
    """
    full_name: Optional[str] = Field(None, min_length=2, max_length=100)
    company_name: Optional[str] = None
    company_size: Optional[str] = None  # NUEVO

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
    # Sistema legacy
    analisis_realizados: int
    cuota_analisis: int
    analisis_restantes: int
    porcentaje_usado: float
    plan: str
    
    # NUEVO: Sistema de créditos
    credits: int
    credits_expire_at: Optional[datetime] = None
    has_valid_credits: bool
    
    puede_analizar: bool

# NUEVO: Schemas para admin
class AddCreditsRequest(BaseModel):
    """
    Schema para agregar créditos a un usuario.
    """
    user_id: int = Field(..., gt=0)
    credits: int = Field(..., gt=0, le=1000, description="Cantidad de créditos a agregar (1-1000)")
    days_valid: int = Field(30, gt=0, le=365, description="Días de validez (1-365)")

class CreateInvitationWithCredits(BaseModel):
    """
    Schema para crear invitación con créditos personalizados.
    """
    email: EmailStr
    initial_credits: int = Field(10, gt=0, le=1000, description="Créditos iniciales (1-1000)")
    credits_valid_days: int = Field(30, gt=0, le=365, description="Días de validez (1-365)")

class UserListResponse(BaseModel):
    """
    Schema para lista de usuarios en admin.
    """
    id: int
    email: str
    full_name: Optional[str]
    company_name: Optional[str]
    company_size: Optional[str]
    is_active: bool
    created_at: datetime
    credits: int
    credits_expire_at: Optional[datetime]
    has_valid_credits: bool
    analisis_realizados: int
    plan: str
    
    class Config:
        from_attributes = True

class AdminDashboardStats(BaseModel):
    """
    Schema para estadísticas del dashboard admin.
    """
    total_users: int
    active_users: int
    total_credits_distributed: int
    users_without_credits: int
    total_invitations: int
    pending_invitations: int
    used_invitations: int
    total_analysis_today: int
    total_analysis_week: int
    total_analysis_month: int
