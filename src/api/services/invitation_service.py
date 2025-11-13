"""
Servicio de lógica de negocio para el sistema de invitaciones.
"""

from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from typing import Optional, List, Dict, Tuple
from datetime import datetime, timedelta

from ..models.invitation import Invitation
from ..models.user import User
from ..schemas.invitation import (
    InvitationCreate,
    InvitationUpdate,
    InvitationResponse,
    InvitationStatsResponse
)
from .email_service import EmailService


class InvitationService:
    """
    Servicio para gestión de invitaciones.
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.email_service = EmailService()
    
    def create_invitation(
        self, 
        data: InvitationCreate, 
        admin_user_id: int
    ) -> Tuple[Optional[Invitation], Optional[str]]:
        """
        Crea una nueva invitación.
        """
        # Verificar si el email ya está registrado
        existing_user = self.db.query(User).filter(User.email == data.email).first()
        if existing_user:
            return None, f"El email {data.email} ya está registrado"
        
        # Verificar si ya existe una invitación activa
        existing_invitation = self.db.query(Invitation).filter(
            and_(
                Invitation.email == data.email,
                Invitation.status.in_(['pending', 'used'])
            )
        ).first()
        
        if existing_invitation:
            if existing_invitation.status == 'pending' and existing_invitation.is_valid():
                return None, f"Ya existe una invitación activa para {data.email}"
            elif existing_invitation.status == 'used':
                return None, f"El email {data.email} ya fue invitado"
        
        # Generar token único
        token = self._generate_unique_token()
        
        # Calcular fecha de expiración
        expires_at = Invitation.calculate_expiration(days=data.expiration_days)
        
        # Crear invitación
        invitation = Invitation(
            email=data.email,
            token=token,
            status="pending",
            plan=data.plan,
            initial_credits=data.initial_credits,
            credits_valid_days=data.credits_valid_days,
            expires_at=expires_at,
            created_by=admin_user_id,
            notes=data.notes,
            initial_credits=data.initial_credits,
            credits_valid_days=data.credits_valid_days
        )
        
        self.db.add(invitation)
        self.db.commit()
        self.db.refresh(invitation)
        
        # Enviar email de invitación
        admin_user = self.db.query(User).filter(User.id == admin_user_id).first()
        admin_name = admin_user.full_name if admin_user and admin_user.full_name else None
        
        user_name = data.email.split('@')[0].replace('.', ' ').title()
        
        success, error = self.email_service.send_invitation_email(
            to_email=data.email,
            to_name=user_name,
            invitation_token=token,
            plan=data.plan,
            cuota_analisis=data.cuota_analisis,
            admin_name=admin_name
        )
        
        if not success:
            print(f"⚠️ Advertencia: No se pudo enviar email a {data.email}: {error}")
        
        return invitation, None
    
    def _generate_unique_token(self, max_attempts: int = 10) -> str:
        """
        Genera un token único.
        """
        for _ in range(max_attempts):
            token = Invitation.generate_token()
            
            exists = self.db.query(Invitation).filter(
                Invitation.token == token
            ).first()
            
            if not exists:
                return token
        
        raise RuntimeError("No se pudo generar un token único")
    
    def validate_token(self, token: str) -> Tuple[bool, Optional[Invitation], Optional[str]]:
        """
        Valida un token de invitación.
        """
        invitation = self.db.query(Invitation).filter(
            Invitation.token == token
        ).first()
        
        if not invitation:
            return False, None, "Token de invitación inválido"
        
        if not invitation.is_valid():
            if invitation.status == "used":
                return False, invitation, "Esta invitación ya fue utilizada"
            elif invitation.status == "expired":
                return False, invitation, "Esta invitación ha expirado"
            elif invitation.status == "revoked":
                return False, invitation, "Esta invitación fue revocada"
            else:
                return False, invitation, "Esta invitación no es válida"
        
        existing_user = self.db.query(User).filter(
            User.email == invitation.email
        ).first()
        
        if existing_user:
            return False, invitation, "El email ya está registrado"
        
        return True, invitation, None
    
    def mark_as_used(self, token: str, user_id: int) -> Tuple[bool, Optional[str]]:
        """
        Marca una invitación como usada.
        """
        invitation = self.db.query(Invitation).filter(
            Invitation.token == token
        ).first()
        
        if not invitation:
            return False, "Invitación no encontrada"
        
        if invitation.status != "pending":
            return False, f"La invitación está en estado '{invitation.status}'"
        
        invitation.mark_as_used(user_id)
        self.db.commit()
        
        return True, None
    
    def revoke_invitation(self, invitation_id: int) -> Tuple[bool, Optional[str]]:
        """
        Revoca una invitación no usada.
        """
        invitation = self.db.query(Invitation).filter(
            Invitation.id == invitation_id
        ).first()
        
        if not invitation:
            return False, "Invitación no encontrada"
        
        if not invitation.revoke():
            return False, "No se puede revocar una invitación usada"
        
        self.db.commit()
        return True, None
    
    def resend_invitation(self, invitation_id: int, new_expiration_days: int = 7) -> Tuple[bool, Optional[str]]:
        """
        Re-envía una invitación extendiendo su expiración.
        """
        invitation = self.db.query(Invitation).filter(
            Invitation.id == invitation_id
        ).first()
        
        if not invitation:
            return False, "Invitación no encontrada"
        
        if invitation.status == "used":
            return False, "No se puede re-enviar una invitación ya usada"
        
        if invitation.status == "revoked":
            return False, "No se puede re-enviar una invitación revocada"
        
        invitation.expires_at = datetime.utcnow() + timedelta(days=new_expiration_days)
        invitation.status = "pending"
        
        self.db.commit()
        
        # Enviar email
        user_name = invitation.email.split('@')[0].replace('.', ' ').title()
        success, error = self.email_service.send_invitation_email(
            to_email=invitation.email,
            to_name=user_name,
            invitation_token=invitation.token,
            plan=invitation.plan,
            initial_credits=invitation.initial_credits,
            credits_valid_days=invitation.credits_valid_days,
            admin_name=None
        )
        
        if not success:
            print(f"⚠️ Advertencia: No se pudo re-enviar email: {error}")
        
        return True, None
    
    def get_invitation_by_id(self, invitation_id: int) -> Optional[Invitation]:
        """
        Obtiene una invitación por ID.
        """
        return self.db.query(Invitation).filter(
            Invitation.id == invitation_id
        ).first()
    
    def get_invitation_by_token(self, token: str) -> Optional[Invitation]:
        """
        Obtiene una invitación por token.
        """
        return self.db.query(Invitation).filter(
            Invitation.token == token
        ).first()
    
    def list_invitations(
        self,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[Invitation], int]:
        """
        Lista invitaciones con paginación.
        """
        query = self.db.query(Invitation)
        
        if status:
            query = query.filter(Invitation.status == status)
        
        total = query.count()
        
        offset = (page - 1) * page_size
        invitations = query.order_by(Invitation.created_at.desc()).offset(offset).limit(page_size).all()
        
        return invitations, total
    
    def get_stats(self) -> InvitationStatsResponse:
        """
        Obtiene estadísticas del sistema de invitaciones.
        """
        stats = self.db.query(
            Invitation.status,
            func.count(Invitation.id)
        ).group_by(Invitation.status).all()
        
        status_counts = {status: count for status, count in stats}
        
        total = sum(status_counts.values())
        pending = status_counts.get('pending', 0)
        used = status_counts.get('used', 0)
        expired = status_counts.get('expired', 0)
        revoked = status_counts.get('revoked', 0)
        
        conversion_rate = (used / total * 100) if total > 0 else 0.0
        
        avg_days = self.db.query(
            func.avg(
                func.extract('epoch', Invitation.used_at) - func.extract('epoch', Invitation.created_at)
            ) / 86400  # Convertir segundos a días
        ).filter(Invitation.status == 'used').scalar()
        
        return InvitationStatsResponse(
            total=total,
            pending=pending,
            used=used,
            expired=expired,
            revoked=revoked,
            conversion_rate=round(conversion_rate, 2),
            avg_days_to_use=round(avg_days, 2) if avg_days else None
        )


