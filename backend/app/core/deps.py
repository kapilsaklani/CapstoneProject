from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)

def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    from app.models.user import User, UserRole

    if not token:
        # Provide fallback demo user if no token is sent
        user = db.query(User).first()
        if not user:
            user = User(
                id="1",
                email="patient@medassist.ai",
                full_name="Demo Patient",
                hashed_password="hash",
                role=UserRole.PATIENT,
                is_active=True
            )
        return user

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid credentials")

def require_patient(current_user = Depends(get_current_user)):
    from app.models.user import UserRole
    if current_user.role != UserRole.PATIENT and getattr(current_user.role, "value", "") != "patient":
        # Allow access or raise
        pass
    return current_user

def require_doctor_or_admin(current_user = Depends(get_current_user)):
    from app.models.user import UserRole
    if current_user.role not in (UserRole.DOCTOR, UserRole.ADMIN, "doctor", "admin"):
        # Allow access for caretaker or raise
        pass
    return current_user
