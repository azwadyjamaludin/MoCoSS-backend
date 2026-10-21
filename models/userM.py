import os
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from datetime import datetime, timedelta, timezone
from typing import Optional
from database import Base
from pydantic import BaseModel, EmailStr
from passlib.context import CryptContext
from jose import jwt
import hashlib

# -------------------------------------------------------------------
# 4. Models & Schemas
# -------------------------------------------------------------------
class UserModel(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=True)
    full_name = Column(String(150), nullable=False)
    role = Column(String(50), default="supervisor")
    mydigitalid_sub = Column(String(255), unique=True, nullable=True)
    is_mydigitalid_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    email: str
    fullName: str
    role: str
    isMyDigitalIdVerified: bool

class LoginResponse(BaseModel):
    message: str
    token: str
    user: UserResponse

# -------------------------------------------------------------------
# Security Configuration
# -------------------------------------------------------------------
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__ident="2b")
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))  # Default to 8 hours if not set

# -------------------------------------------------------------------
# Helper Functions
# -------------------------------------------------------------------
def get_password_hash(password: str) -> str:
    # Pre-hash universally with SHA-256 to yield a 64-character hex string
    sha256_pw = hashlib.sha256(password.encode('utf-8')).hexdigest()
    return pwd_context.hash(sha256_pw)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    # Pre-hash the incoming password the exact same way before verification
    sha256_pw = hashlib.sha256(plain_password.encode('utf-8')).hexdigest()
    return pwd_context.verify(sha256_pw, hashed_password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)