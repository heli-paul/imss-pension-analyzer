"""
Servicio de autenticación con soporte de invitaciones.
"""

from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional, Tuple

from ..models.user import User
from ..schemas.user import UserCreate
from .security import hash_password, verify_password, create_access_token


class AuthService:
    """
    Servicio para autenticación y gestión de usuarios.
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """
        Obtiene un usuario por email.
        """
        return self.db.query(User).filter(User.email == email).first()
    
    def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """
        Autentica un usuario con email y contraseña.
        """
        user = self.get_user_by_email(email)
        if not user:
            return None
        
        if not verify_password(password, user.hashed_password):
            return None
        
        return user
    
    def create_user(self, user_data: UserCreate) -> User:
        """
        Crea un nuevo usuario (método legacy - sin invitación).
        """
        user = User(
            email=user_data.email,
            hashed_password=hash_password(user_data.password),
            full_name=user_data.full_name,
            plan="free",
            cuota_analisis=30,
            analisis_realizados=0,
            is_active=True
        )
        
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        
        return user
    
    def register_user_with_invitation(
        self,
        email: str,
        password: str,
        full_name: Optional[str],
        company_name: Optional[str],
        invitation_token: str,
        plan: str,
        cuota_analisis: int
    ) -> Tuple[Optional[User], Optional[str]]:
        """
        Registra un nuevo usuario usando una invitación.
        """
        # Verificar si el usuario ya existe
        existing_user = self.get_user_by_email(email)
        if existing_user:
            return None, "El email ya está registrado"
        
        # Crear usuario con datos de la invitación
        hashed_password = hash_password(password)
        
        new_user = User(
            email=email,
            full_name=full_name,
            # company_name=company_name,
            hashed_password=hashed_password,
            plan=plan,
            cuota_analisis=cuota_analisis,
            invitation_token=invitation_token,
            is_active=True,
            analisis_realizados=0
        )
        
        self.db.add(new_user)
        self.db.commit()
        self.db.refresh(new_user)
        
        return new_user, None
    
    def increment_usage(self, user: User) -> bool:
        """
        Incrementa el contador de análisis del usuario.
        """
        if not user.can_analyze():
            return False
        
        user.analisis_realizados += 1
        self.db.commit()
        
        return True
    
    def get_password_hash(self, password: str) -> str:
        """
        Genera hash de contraseña.
        """
        return hash_password(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """
        Verifica una contraseña contra su hash.
        """
        return verify_password(plain_password, hashed_password)

