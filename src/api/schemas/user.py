from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None

class UserCreate(UserBase):
    password: str
    company_name: Optional[str] = None  # NUEVO

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(UserBase):
    id: int
    company_name: Optional[str] = None  # NUEVO
    plan: str
    monthly_quota: int
    usage_count: int
    spreadsheet_id: Optional[str] = None  # NUEVO
    spreadsheet_url: Optional[str] = None  # NUEVO
    sheet_created_at: Optional[datetime] = None  # NUEVO
    created_at: datetime
    is_active: bool
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse




