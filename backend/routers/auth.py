from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.security import create_access_token, hash_password, verify_password
from app.models.profile import DoctorProfile, PatientProfile
from app.models.user import User, UserRole
from app.schemas.auth import Token, UserLogin, UserOut, UserRegister

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
def register(payload: UserRegister, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        email=payload.email,
        hashed_password=hash_password(payload.password),
        full_name=payload.full_name,
        role=payload.role,
    )
    db.add(user)
    db.flush()

    if payload.role == UserRole.PATIENT:
        db.add(
            PatientProfile(
                user_id=user.id,
                date_of_birth=payload.date_of_birth,
                sex=payload.sex,
            )
        )
    elif payload.role == UserRole.DOCTOR:
        db.add(
            DoctorProfile(
                user_id=user.id,
                specialization=payload.specialization,
                license_number=payload.license_number,
            )
        )

    db.commit()

    token = create_access_token(subject=user.id, role=user.role.value)
    return Token(access_token=token, role=user.role.value, user_id=user.id, full_name=user.full_name)


@router.post("/login", response_model=Token)
def login(payload: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is deactivated")

    token = create_access_token(subject=user.id, role=user.role.value)
    return Token(access_token=token, role=user.role.value, user_id=user.id, full_name=user.full_name)


@router.get("/me", response_model=UserOut)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user
