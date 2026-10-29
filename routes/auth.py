from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from database import SessionLocal
from models.fskRegistry import (
    FskRegistryModel,
    LookupResponse,
    RegisterRequest,
)
from models.userM import (
    LoginRequest,
    LoginResponse,
    UserResponse,
    UserModel,
    get_password_hash,
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
    
    print(f"DEBUG: Attempted login for {request.email} with password '{request.password}'")
    user = db.query(UserModel).filter(UserModel.email == request.email).first()

    if user:
        print(f"DEBUG: Found user in DB. Stored hash: {user.hashed_password}")

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password."
        )

    if not user.hashed_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Account configured for MyDigital ID login only."
        )

    if not verify_password(request.password, user.hashed_password):
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
            isMyDID=user.is_mydid
        )
    )

def _normalize_id(identifier: str) -> str:
    return identifier.strip().upper()


@router.get("/lookup", response_model=LookupResponse)
def lookup_identifier(id: str, db: Session = Depends(get_db)):
    """Used by the Register screen to auto-fill name / email / role from the FSK registry."""
    entry = (
        db.query(FskRegistryModel)
        .filter(FskRegistryModel.identifier == _normalize_id(id))
        .first()
    )
    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ID not found in FSK database."
        )
    if entry.user_id is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This ID is already registered."
        )
    return LookupResponse(fullName=entry.full_name, email=entry.email, role=entry.role)


@router.post("/register", response_model=LoginResponse, status_code=status.HTTP_201_CREATED)
def register(request: RegisterRequest, db: Session = Depends(get_db)):
    """Create an account for a person listed in fsk_registry, then log them in."""
    entry = (
        db.query(FskRegistryModel)
        .filter(FskRegistryModel.identifier == _normalize_id(request.identifier))
        .with_for_update()
        .first()
    )
    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ID not found in FSK database."
        )
    if entry.user_id is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This ID is already registered."
        )

    taken = (
        db.query(UserModel)
        .filter((UserModel.email == entry.email) | (UserModel.username == entry.identifier))
        .first()
    )
    if taken:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email or ID already exists."
        )

    # Name, email and role come from the registry, never from the client.
    user = UserModel(
        username=entry.identifier,
        email=entry.email,
        full_name=entry.full_name,
        hashed_password=get_password_hash(request.password),
        role=entry.role,
    )
    try:
        db.add(user)
        db.flush()            # assigns user.id
        entry.user_id = user.id
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email or ID already exists."
        )
    db.refresh(user)

    access_token = create_access_token(
        data={"sub": str(user.id), "email": user.email, "role": user.role}
    )
    return LoginResponse(
        message="Registration successful",
        token=access_token,
        user=UserResponse(
            id=user.id,
            email=user.email,
            fullName=user.full_name,
            role=user.role,
            isMyDID=bool(user.is_mydid)
        )
    )


@router.post("/mydigitalid")
def mydigitalid_placeholder():
    """Placeholder endpoint for future MyDigital ID authentication."""
    return {
        "status": "ready",
        "message": "MyDigital ID authentication endpoint prepared for future activation."
    }