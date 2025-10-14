"""
Rutas de autenticación actualizadas con sistema de invitaciones.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas.user import (
    UserRegister,
    UserLogin,
    UserResponse,
    Token,
    UserChangePassword,
    UserStatsResponse
)
from ..schemas.invitation import (
    InvitationValidateRequest,
    InvitationValidateResponse
)
from ..services.auth_service import AuthService
from ..services.security import get_current_user, create_access_token
from ..services.invitation_service import InvitationService
from ..models.user import User

router = APIRouter(
    prefix="/auth",
    tags=["auth"]
)


@router.post("/validate-token", response_model=InvitationValidateResponse)
async def validate_invitation_token(
    data: InvitationValidateRequest,
    db: Session = Depends(get_db)
):
    """
    Valida un token de invitación sin autenticación.
    
    Endpoint público para que el frontend verifique el token
    antes de mostrar el formulario de registro.
    """
    service = InvitationService(db)
    
    is_valid, invitation, error_message = service.validate_token(data.token)
    
    if not is_valid:
        return InvitationValidateResponse(
            is_valid=False,
            error_message=error_message
        )
    
    return InvitationValidateResponse(
        is_valid=True,
        email=invitation.email,
        plan=invitation.plan,
        cuota_analisis=invitation.cuota_analisis,
        expires_at=invitation.expires_at
    )


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserRegister,
    db: Session = Depends(get_db)
):
    """
    Registra un nuevo usuario con token de invitación.
    
    El token de invitación es OBLIGATORIO.
    """
    # 1. Validar token de invitación
    invitation_service = InvitationService(db)
    is_valid, invitation, error = invitation_service.validate_token(user_data.invitation_token)
    
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error or "Token de invitación inválido"
        )
    
    # 2. Verificar que el email coincida
    if invitation.email != user_data.email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El email no coincide con la invitación"
        )
    
    # 3. Crear usuario
    auth_service = AuthService(db)
    
    user, error = auth_service.register_user_with_invitation(
        email=user_data.email,
        password=user_data.password,
        full_name=user_data.full_name,
        company_name=user_data.company_name,
        invitation_token=user_data.invitation_token,
        plan=invitation.plan,
        cuota_analisis=invitation.cuota_analisis
    )
    
    if error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error
        )
    
    # 4. Marcar invitación como usada
    success, error = invitation_service.mark_as_used(
        token=user_data.invitation_token,
        user_id=user.id
    )
    
    if not success:
        # No fallar registro si no se puede marcar invitación
        print(f"⚠️ Advertencia: No se pudo marcar invitación como usada: {error}")
    
    # 5. Generar token JWT
    access_token = create_access_token(data={"sub": user.email})
    
    # 6. Enviar email de bienvenida
    from ..services.email_service import EmailService
    email_service = EmailService()
    
    user_name = user.full_name or user.email.split('@')[0].replace('.', ' ').title()
    success, error = email_service.send_welcome_email(
        to_email=user.email,
        to_name=user_name,
        plan=user.plan
    )
    
    if not success:
        print(f"⚠️ Advertencia: No se pudo enviar email de bienvenida: {error}")
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.model_validate(user)
    )


@router.post("/login/json", response_model=Token)
async def login(
    user_data: UserLogin,
    db: Session = Depends(get_db)
):
    """
    Autenticación con email y contraseña (formato JSON).
    """
    auth_service = AuthService(db)
    
    user = auth_service.authenticate_user(
        email=user_data.email,
        password=user_data.password
    )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o contraseña incorrectos"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario desactivado"
        )
    
    access_token = create_access_token(data={"sub": user.email})
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.model_validate(user)
    )


@router.post("/login", response_model=Token)
async def login_form(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Autenticación con email y contraseña (formato OAuth2).
    
    Compatible con herramientas que usan OAuth2PasswordRequestForm.
    """
    auth_service = AuthService(db)
    
    user = auth_service.authenticate_user(
        email=form_data.username,  # OAuth2 usa 'username'
        password=form_data.password
    )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario desactivado"
        )
    
    access_token = create_access_token(data={"sub": user.email})
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.model_validate(user)
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """
    Obtiene la información del usuario autenticado.
    """
    return UserResponse.model_validate(current_user)


@router.get("/me/stats", response_model=UserStatsResponse)
async def get_user_stats(
    current_user: User = Depends(get_current_user)
):
    """
    Obtiene estadísticas de uso del usuario.
    """
    analisis_restantes = current_user.cuota_analisis - current_user.analisis_realizados
    porcentaje_usado = (
        (current_user.analisis_realizados / current_user.cuota_analisis * 100)
        if current_user.cuota_analisis > 0
        else 0
    )
    
    return UserStatsResponse(
        analisis_realizados=current_user.analisis_realizados,
        cuota_analisis=current_user.cuota_analisis,
        analisis_restantes=analisis_restantes,
        porcentaje_usado=round(porcentaje_usado, 2),
        plan=current_user.plan,
        puede_analizar=current_user.can_analyze()
    )


@router.post("/change-password")
async def change_password(
    data: UserChangePassword,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Cambia la contraseña del usuario autenticado.
    """
    from .security import verify_password, hash_password
    
    # Verificar contraseña actual
    if not verify_password(data.old_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Contraseña actual incorrecta"
        )
    
    # Actualizar contraseña
    current_user.hashed_password = hash_password(data.new_password)
    db.commit()
    
    return {
        "message": "Contraseña actualizada exitosamente"
    }


@router.post("/refresh", response_model=Token)
async def refresh_token(
    current_user: User = Depends(get_current_user)
):
    """
    Genera un nuevo token de acceso para el usuario autenticado.
    """
    access_token = create_access_token(data={"sub": current_user.email})
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.model_validate(current_user)
    )


