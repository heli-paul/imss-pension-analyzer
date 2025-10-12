from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional

from ..models.user import User
from ..schemas.user import UserCreate
from .security import hash_password, verify_password, create_access_token

class AuthService:
    def __init__(self, db: Session):
        self.db = db
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """Obtener usuario por email"""
        return self.db.query(User).filter(User.email == email).first()
    
    def create_user(self, user_data: UserCreate) -> User:
        """Crear nuevo usuario"""
        # Crear usuario con plan free (10 análisis gratis)
        user = User(
            email=user_data.email,
            hashed_password=hash_password(user_data.password),
            full_name=user_data.full_name,
            plan="free",
            monthly_quota=30,
            usage_count=0,
        )
        
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        
        return user
    
    def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """Autenticar usuario (login)"""
        user = self.get_user_by_email(email)
        
        if not user:
            return None
        
        if not verify_password(password, user.hashed_password):
            return None
        
        return user
    
    def increment_usage(self, user: User):
        """Incrementar contador de uso"""
        user.usage_count += 1
        self.db.commit()


