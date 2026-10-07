"""
routes/auth.py - Authentication API Routes
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import SessionLocal
from main import (
    LoginRequest,
    LoginResponse,
    UserResponse,
    UserModel,
    verify_password,
    create_access_token,
)

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/login", response_model=LoginResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    """Authenticates a user with email and password, returning a JWT token."""
    user = db.query(UserModel).filter(UserModel.email == request.email).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password."
        )

    if not user.password_hash:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Account configured for MyDigital ID login only."
        )

    if not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password."
        )

    access_token = create_access_token(
        data={"sub": str(user.id), "email": user.email, "role": user.role}
    )

    return LoginResponse(
        message="Login successful",
        token=access_token,
        user=UserResponse(
            id=user.id,
            email=user.email,
            fullName=user.full_name,
            role=user.role,
            isMyDigitalIdVerified=user.is_mydigitalid_verified or False
        )
    )

@router.post("/mydigitalid")
def mydigitalid_placeholder():
    """Placeholder endpoint for future MyDigital ID authentication."""
    return {
        "status": "ready",
        "message": "MyDigital ID authentication endpoint prepared for future activation."
    }