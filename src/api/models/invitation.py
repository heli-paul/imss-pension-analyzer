"""
Modelo SQLAlchemy para el sistema de invitaciones con tokens.

Este modelo maneja el flujo de whitelisting de usuarios:
1. Admin crea invitación con email y parámetros
2. Sistema genera token único y seguro
3. Usuario registra usando el token
4. Token se marca como usado y se asocia al usuario
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime, timedelta
import secrets

from ..database import Base


class Invitation(Base):
    """
    Modelo de invitación para control de acceso (whitelisting).
    
    Attributes:
        id: ID único de la invitación
        email: Email del invitado (único, para evitar duplicados)
        token: Token único y seguro para el link de registro
        status: Estado actual (pending, used, expired, revoked)
        plan: Plan asignado al usuario (free, basic, premium)
        cuota_analisis: Número de análisis permitidos
        created_at: Fecha de creación
        expires_at: Fecha de expiración (default: 7 días)
        used_at: Fecha en que se usó el token (null si no usado)
        user_id: ID del usuario que usó la invitación (null hasta registro)
        created_by: ID del admin que creó la invitación
        notes: Notas internas del admin sobre esta invitación
    """
    
    __tablename__ = "invitations"
    
    # Identificadores
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    token = Column(String(64), unique=True, nullable=False, index=True)
    
    # Estado y configuración
    status = Column(
        String(20), 
        default="pending", 
        nullable=False,
        index=True
    )  # pending, used, expired, revoked
    
    plan = Column(String(20), default="free", nullable=False)
    cuota_analisis = Column(Integer, default=30, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    used_at = Column(DateTime, nullable=True)
    
    # Relaciones
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Notas internas
    notes = Column(Text, nullable=True)
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id], back_populates="invitation")
    creator = relationship("User", foreign_keys=[created_by])
    
    @classmethod
    def generate_token(cls) -> str:
        """
        Genera un token seguro para la invitación.
        
        Formato: inv_XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
        Usa secrets.token_urlsafe para seguridad criptográfica.
        
        Returns:
            Token único de 64 caracteres con prefijo 'inv_'
        """
        return f"inv_{secrets.token_urlsafe(32)}"
    
    @classmethod
    def calculate_expiration(cls, days: int = 7) -> datetime:
        """
        Calcula la fecha de expiración para una invitación.
        
        Args:
            days: Número de días hasta expiración (default: 7)
            
        Returns:
            datetime de expiración
        """
        return datetime.utcnow() + timedelta(days=days)
    
    def is_valid(self) -> bool:
        """
        Verifica si la invitación es válida para uso.
        
        Una invitación es válida si:
        - Estado es 'pending'
        - No ha expirado
        - No ha sido usada
        
        Returns:
            True si la invitación es válida, False en caso contrario
        """
        if self.status != "pending":
            return False
        
        if self.expires_at < datetime.utcnow():
            # Auto-marcar como expirada
            self.status = "expired"
            return False
        
        if self.used_at is not None:
            return False
        
        return True
    
    def mark_as_used(self, user_id: int) -> None:
        """
        Marca la invitación como usada.
        
        Args:
            user_id: ID del usuario que usó la invitación
        """
        self.status = "used"
        self.used_at = datetime.utcnow()
        self.user_id = user_id
    
    def revoke(self) -> bool:
        """
        Revoca una invitación no usada.
        
        Returns:
            True si se pudo revocar, False si ya fue usada
        """
        if self.status == "used":
            return False
        
        self.status = "revoked"
        return True
    
    def to_dict(self) -> dict:
        """
        Convierte la invitación a diccionario para API responses.
        
        Returns:
            Diccionario con todos los campos de la invitación
        """
        return {
            "id": self.id,
            "email": self.email,
            "token": self.token,
            "status": self.status,
            "plan": self.plan,
            "cuota_analisis": self.cuota_analisis,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "used_at": self.used_at.isoformat() if self.used_at else None,
            "user_id": self.user_id,
            "created_by": self.created_by,
            "notes": self.notes,
            "is_valid": self.is_valid()
        }
    
    def __repr__(self):
        return f"<Invitation(email='{self.email}', status='{self.status}')>"


