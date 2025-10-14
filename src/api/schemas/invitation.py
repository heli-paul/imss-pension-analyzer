"""
Pydantic schemas para validación de datos de invitaciones.
"""

from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional
from datetime import datetime


class InvitationCreate(BaseModel):
    """
    Schema para crear una nueva invitación.
    """
    email: EmailStr = Field(..., description="Email del usuario a invitar")
    plan: str = Field(default="free", pattern="^(free|basic|premium)$")
    cuota_analisis: int = Field(default=30, ge=1, le=1000)
    expiration_days: int = Field(default=7, ge=1, le=90)
    notes: Optional[str] = Field(default=None, max_length=500)
    
    @field_validator('plan')
    @classmethod
    def validate_plan(cls, v: str) -> str:
        allowed_plans = ['free', 'basic', 'premium']
        if v not in allowed_plans:
            raise ValueError(f'Plan debe ser uno de: {", ".join(allowed_plans)}')
        return v


class InvitationUpdate(BaseModel):
    """
    Schema para actualizar una invitación existente.
    """
    notes: Optional[str] = Field(default=None, max_length=500)
    expiration_days: Optional[int] = Field(default=None, ge=1, le=90)


class InvitationResponse(BaseModel):
    """
    Schema para respuestas de API con información de invitación.
    """
    id: int
    email: str
    token: str
    status: str
    plan: str
    cuota_analisis: int
    created_at: datetime
    expires_at: datetime
    used_at: Optional[datetime] = None
    user_id: Optional[int] = None
    created_by: int
    notes: Optional[str] = None
    is_valid: bool
    invitation_url: Optional[str] = None
    
    class Config:
        from_attributes = True


class InvitationListResponse(BaseModel):
    """
    Schema para lista paginada de invitaciones.
    """
    invitations: list[InvitationResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class InvitationValidateRequest(BaseModel):
    """
    Schema para validar un token de invitación.
    """
    token: str = Field(..., min_length=10)


class InvitationValidateResponse(BaseModel):
    """
    Schema para respuesta de validación de token.
    """
    is_valid: bool
    email: Optional[str] = None
    plan: Optional[str] = None
    cuota_analisis: Optional[int] = None
    expires_at: Optional[datetime] = None
    error_message: Optional[str] = None


class InvitationStatsResponse(BaseModel):
    """
    Schema para estadísticas de invitaciones.
    """
    total: int
    pending: int
    used: int
    expired: int
    revoked: int
    conversion_rate: float
    avg_days_to_use: Optional[float] = None


class BulkInvitationCreate(BaseModel):
    """
    Schema para crear múltiples invitaciones.
    """
    emails: list[EmailStr] = Field(..., min_length=1, max_length=50)
    plan: str = Field(default="free", pattern="^(free|basic|premium)$")
    cuota_analisis: int = Field(default=30, ge=1, le=1000)
    expiration_days: int = Field(default=7, ge=1, le=90)
    notes: Optional[str] = Field(default=None, max_length=500)


class BulkInvitationResponse(BaseModel):
    """
    Schema para respuesta de invitaciones masivas.
    """
    created: list[InvitationResponse]
    skipped: list[dict]
    total_created: int
    total_skipped: int



