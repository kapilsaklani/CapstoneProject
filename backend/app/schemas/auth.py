from typing import Optional
from datetime import date
from pydantic import BaseModel
from app.models.user import UserRole

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    user_id: str
    full_name: str

class UserLogin(BaseModel):
    email: str
    password: str

class UserRegister(BaseModel):
    email: str
    password: str
    full_name: str
    role: UserRole = UserRole.PATIENT
    date_of_birth: Optional[date] = None
    sex: Optional[str] = None
    specialization: Optional[str] = None
    license_number: Optional[str] = None

class UserOut(BaseModel):
    id: str
    email: str
    full_name: str
    role: UserRole
    is_active: bool

    class Config:
        from_attributes = True
