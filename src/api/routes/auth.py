from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import logging

from ..database import get_db
from ..schemas.user import UserCreate, UserResponse, Token, UserLogin
from ..services.auth_service import AuthService
from ..services.user_sheets_service import UserSheetsService
from ..services.security import get_current_user
from ..services.security import get_current_user, create_access_token  # ← IMPORTANTE: agregar create_access_token
from ..models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Autenticación"])

@router.post("/register", response_model=Token)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """
    Registrar nuevo usuario y crear automáticamente su Google Sheet personal
    """
    auth_service = AuthService(db)

    # Verificar si el email ya existe
    existing_user = auth_service.get_user_by_email(user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El email ya está registrado"
        )

    try:
        # Crear usuario en la base de datos
        new_user = auth_service.create_user(user_data)
        logger.info(f"✅ Usuario creado: {new_user.email}")

        # Crear Google Sheet personal para el usuario
        sheets_service = UserSheetsService()
        spreadsheet_id, spreadsheet_url, success = sheets_service.crear_sheet_para_usuario(
            user_email=new_user.email,
            company_name=user_data.company_name
        )

        if success:
            # Guardar información del sheet en el usuario
            new_user.spreadsheet_id = spreadsheet_id
            new_user.spreadsheet_url = spreadsheet_url
            new_user.sheet_created_at = datetime.now()
            db.commit()
            db.refresh(new_user)
            logger.info(f"✅ Google Sheet creado para {new_user.email}: {spreadsheet_id}")
            logger.info(f"🔗 URL: {spreadsheet_url}")
        else:
            logger.warning(f"⚠️ No se pudo crear Google Sheet para {new_user.email}")

        # Crear token de acceso
        access_token = create_access_token(data={"sub": new_user.email})
        
        logger.info(f"✅ Registro completo: {new_user.email}")

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": new_user
        }

    except Exception as e:
        logger.error(f"❌ Error en registro: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al crear usuario: {str(e)}"
        )

@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Login de usuario usando OAuth2PasswordRequestForm (form-data)
    """
    auth_service = AuthService(db)

    # Autenticar usuario (form_data.username contiene el email)
    user = auth_service.authenticate_user(form_data.username, form_data.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario inactivo"
        )

    # Crear token de acceso
    access_token = create_access_token(data={"sub": user.email})

    logger.info(f"✅ Login exitoso: {user.email}")

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }

@router.post("/login/json", response_model=Token)
async def login_json(
    credentials: UserLogin,
    db: Session = Depends(get_db)
):
    """
    Login de usuario usando JSON (para frontend)
    """
    auth_service = AuthService(db)

    # Autenticar usuario
    user = auth_service.authenticate_user(credentials.email, credentials.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario inactivo"
        )

    # Crear token de acceso
    access_token = create_access_token(data={"sub": user.email})

    logger.info(f"✅ Login exitoso (JSON): {user.email}")

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """
    Obtener información del usuario autenticado
    """
    return current_user

@router.get("/my-sheet")
async def get_my_sheet(current_user: User = Depends(get_current_user)):
    """
    Obtener información del Google Sheet personal del usuario
    """
    if not current_user.spreadsheet_id:
        return {
            "has_sheet": False,
            "message": "No tienes un Google Sheet asignado todavía"
        }

    return {
        "has_sheet": True,
        "spreadsheet_id": current_user.spreadsheet_id,
        "spreadsheet_url": current_user.spreadsheet_url,
        "created_at": current_user.sheet_created_at,
        "message": "Tu Google Sheet personal está listo"
    }

@router.post("/create-sheet")
async def create_sheet_for_user(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Crear Google Sheet para un usuario que no lo tiene
    """
    if current_user.spreadsheet_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya tienes un Google Sheet asignado"
        )

    try:
        sheets_service = UserSheetsService()
        spreadsheet_id, spreadsheet_url, success = sheets_service.crear_sheet_para_usuario(
            user_email=current_user.email,
            company_name=current_user.company_name
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="No se pudo crear el Google Sheet"
            )

        # Actualizar usuario
        current_user.spreadsheet_id = spreadsheet_id
        current_user.spreadsheet_url = spreadsheet_url
        current_user.sheet_created_at = datetime.now()
        db.commit()

        logger.info(f"✅ Google Sheet creado manualmente para {current_user.email}")

        return {
            "success": True,
            "spreadsheet_id": spreadsheet_id,
            "spreadsheet_url": spreadsheet_url,
            "message": "Google Sheet creado exitosamente"
        }

    except Exception as e:
        logger.error(f"❌ Error creando sheet: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al crear Google Sheet: {str(e)}"
        )

@router.put("/update-profile")
async def update_profile(
    full_name: str = None,
    company_name: str = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Actualizar información del perfil del usuario
    """
    try:
        if full_name:
            current_user.full_name = full_name

        if company_name:
            current_user.company_name = company_name

        db.commit()
        db.refresh(current_user)

        logger.info(f"✅ Perfil actualizado: {current_user.email}")

        return {
            "success": True,
            "message": "Perfil actualizado exitosamente",
            "user": {
                "email": current_user.email,
                "full_name": current_user.full_name,
                "company_name": current_user.company_name
            }
        }

    except Exception as e:
        logger.error(f"❌ Error actualizando perfil: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al actualizar perfil: {str(e)}"
        )

@router.get("/stats")
async def get_user_stats(current_user: User = Depends(get_current_user)):
    """
    Obtener estadísticas del usuario
    """
    return {
        "email": current_user.email,
        "full_name": current_user.full_name,
        "company_name": current_user.company_name,
        "plan": current_user.plan,
        "usage": {
            "total_quota": current_user.monthly_quota,
            "used": current_user.usage_count,
            "remaining": current_user.monthly_quota - current_user.usage_count,
            "percentage": round((current_user.usage_count / current_user.monthly_quota) * 100, 2)
        },
        "google_sheet": {
            "has_sheet": bool(current_user.spreadsheet_id),
            "url": current_user.spreadsheet_url,
            "created_at": current_user.sheet_created_at
        },
        "account": {
            "is_active": current_user.is_active,
            "is_verified": current_user.is_verified,
            "created_at": current_user.created_at
        }
    }


