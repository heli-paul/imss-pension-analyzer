"""
Modelo SQLAlchemy actualizado para usuarios con soporte de invitaciones.
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from ..database import Base


class User(Base):
    """
    Modelo de usuario del sistema.
    """
    
    __tablename__ = "users"
    
    # Identificadores y autenticación
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    full_name = Column(String(255), nullable=True)
    company_name = Column(String(255))
    hashed_password = Column(String, nullable=False)
    
    # Estado y permisos
    is_active = Column(Boolean, default=True, nullable=False)
    is_admin = Column(Boolean, default=False, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Plan y cuotas
    plan = Column(String(20), default="free", nullable=False)
    analisis_realizados = Column(Integer, default=0, nullable=False)
    cuota_analisis = Column(Integer, default=30, nullable=False)
    
    # Google Sheets integration
    spreadsheet_id = Column(String(255), nullable=True)
    spreadsheet_url = Column(String(512), nullable=True)
    
    # Sistema de invitaciones (NUEVO)
    invited_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    invitation_token = Column(String(64), nullable=True)
    
    # Relationships
    # invitation = relationship("Invitation", foreign_keys="Invitation.user_id", back_populates="user")
    inviter = relationship("User", remote_side=[id], foreign_keys=[invited_by])
    
    def is_admin_user(self) -> bool:
        """
        Verifica si el usuario es administrador.
        """
        admin_emails = [
            "info@todopension.com",
            "heli_paul@todopension.com",
            "contacto@pensionasoft.com"
        ]
        return self.email in admin_emails or self.is_admin
    
    def can_analyze(self) -> bool:
        """
        Verifica si el usuario puede realizar más análisis.
        """
        return self.analisis_realizados < self.cuota_analisis
    
    def increment_analysis_count(self) -> bool:
        """
        Incrementa el contador de análisis realizados.
        """
        if not self.can_analyze():
            return False
        
        self.analisis_realizados += 1
        return True
    
    def reset_analysis_count(self) -> None:
        """
        Resetea el contador de análisis.
        """
        self.analisis_realizados = 0
    
    def to_dict(self, include_sensitive: bool = False) -> dict:
        """
        Convierte el usuario a diccionario.
        """
        data = {
            "id": self.id,
            "email": self.email,
            "full_name": self.full_name,
            "is_active": self.is_active,
            "is_admin": self.is_admin_user(),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "plan": self.plan,
            "analisis_realizados": self.analisis_realizados,
            "cuota_analisis": self.cuota_analisis,
            "can_analyze": self.can_analyze()
        }
        
        if include_sensitive:
            data.update({
                "spreadsheet_id": self.spreadsheet_id,
                "spreadsheet_url": self.spreadsheet_url,
                "invited_by": self.invited_by,
                "invitation_token": self.invitation_token
            })
        
        return data
    
    def __repr__(self):
        return f"<User(email='{self.email}', plan='{self.plan}')>"



