"""
Rutas de administración para gestión de invitaciones.
Solo accesibles para usuarios administradores.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional

from ..database import get_db
from ..models.user import User
from ..schemas.invitation import (
    InvitationCreate,
    InvitationResponse,
    InvitationListResponse,
    InvitationStatsResponse,
    BulkInvitationCreate,
    BulkInvitationResponse
)
from ..services.invitation_service import InvitationService
from ..services.security import get_current_user

router = APIRouter(
    prefix="/admin",
    tags=["admin"]
)


def get_admin_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Dependency para verificar que el usuario es administrador.
    """
    if not current_user.is_admin_user():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos de administrador"
        )
    return current_user


@router.post("/invitations", response_model=InvitationResponse, status_code=status.HTTP_201_CREATED)
async def create_invitation(
    data: InvitationCreate,
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """
    Crea una nueva invitación y envía email al usuario.
    
    Solo accesible para administradores.
    """
    service = InvitationService(db)
    
    invitation, error = service.create_invitation(
        data=data,
        admin_user_id=admin_user.id
    )
    
    if error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error
        )
    
    # Construir URL completa de invitación
    from ..config import get_settings
    settings = get_settings()
    invitation_url = f"{settings.FRONTEND_URL}/register?token={invitation.token}"
    
    response = InvitationResponse.model_validate(invitation)
    response.invitation_url = invitation_url
    
    return response


@router.get("/invitations", response_model=InvitationListResponse)
async def list_invitations(
    status: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """
    Lista todas las invitaciones con paginación.
    
    Query params:
    - status: Filtrar por estado (pending, used, expired, revoked)
    - page: Número de página (default: 1)
    - page_size: Tamaño de página (default: 20)
    """
    if page < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El número de página debe ser mayor a 0"
        )
    
    if page_size < 1 or page_size > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El tamaño de página debe estar entre 1 y 100"
        )
    
    if status and status not in ['pending', 'used', 'expired', 'revoked']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Estado inválido. Opciones: pending, used, expired, revoked"
        )
    
    service = InvitationService(db)
    invitations, total = service.list_invitations(
        status=status,
        page=page,
        page_size=page_size
    )
    
    # Construir URLs y validar estado
    from ..config import get_settings
    settings = get_settings()
    
    invitation_responses = []
    for inv in invitations:
        response = InvitationResponse.model_validate(inv)
        response.invitation_url = f"{settings.FRONTEND_URL}/register?token={inv.token}"
        invitation_responses.append(response)
    
    total_pages = (total + page_size - 1) // page_size
    
    return InvitationListResponse(
        invitations=invitation_responses,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.get("/invitations/{invitation_id}", response_model=InvitationResponse)
async def get_invitation(
    invitation_id: int,
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """
    Obtiene los detalles de una invitación específica.
    """
    service = InvitationService(db)
    invitation = service.get_invitation_by_id(invitation_id)
    
    if not invitation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invitación no encontrada"
        )
    
    from ..config import get_settings
    settings = get_settings()
    
    response = InvitationResponse.model_validate(invitation)
    response.invitation_url = f"{settings.FRONTEND_URL}/register?token={invitation.token}"
    
    return response


@router.post("/invitations/{invitation_id}/revoke", response_model=InvitationResponse)
async def revoke_invitation(
    invitation_id: int,
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """
    Revoca una invitación que no ha sido usada.
    """
    service = InvitationService(db)
    
    success, error = service.revoke_invitation(invitation_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error
        )
    
    invitation = service.get_invitation_by_id(invitation_id)
    
    response = InvitationResponse.model_validate(invitation)
    
    return response


@router.post("/invitations/{invitation_id}/resend", response_model=InvitationResponse)
async def resend_invitation(
    invitation_id: int,
    expiration_days: int = 7,
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """
    Re-envía una invitación extendiendo su fecha de expiración.
    
    Query params:
    - expiration_days: Días de validez (default: 7)
    """
    if expiration_days < 1 or expiration_days > 90:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Los días de expiración deben estar entre 1 y 90"
        )
    
    service = InvitationService(db)
    
    success, error = service.resend_invitation(
        invitation_id=invitation_id,
        new_expiration_days=expiration_days
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error
        )
    
    invitation = service.get_invitation_by_id(invitation_id)
    
    from ..config import get_settings
    settings = get_settings()
    
    response = InvitationResponse.model_validate(invitation)
    response.invitation_url = f"{settings.FRONTEND_URL}/register?token={invitation.token}"
    
    return response


@router.get("/invitations/stats/summary", response_model=InvitationStatsResponse)
async def get_invitation_stats(
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """
    Obtiene estadísticas del sistema de invitaciones.
    """
    service = InvitationService(db)
    stats = service.get_stats()
    
    return stats


@router.post("/invitations/bulk", response_model=BulkInvitationResponse)
async def create_bulk_invitations(
    data: BulkInvitationCreate,
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """
    Crea múltiples invitaciones de una vez.
    
    Útil para invitar varios usuarios con la misma configuración.
    """
    service = InvitationService(db)
    
    created = []
    skipped = []
    
    for email in data.emails:
        invitation_data = InvitationCreate(
            email=email,
            plan=data.plan,
            cuota_analisis=data.cuota_analisis,
            expiration_days=data.expiration_days,
            notes=data.notes
        )
        
        invitation, error = service.create_invitation(
            data=invitation_data,
            admin_user_id=admin_user.id
        )
        
        if invitation:
            from ..config import get_settings
            settings = get_settings()
            
            response = InvitationResponse.model_validate(invitation)
            response.invitation_url = f"{settings.FRONTEND_URL}/register?token={invitation.token}"
            
            created.append(response)
        else:
            skipped.append({
                "email": email,
                "reason": error
            })
    
    return BulkInvitationResponse(
        created=created,
        skipped=skipped,
        total_created=len(created),
        total_skipped=len(skipped)
    )


