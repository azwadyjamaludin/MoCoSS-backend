# This is the Main FastAPI Application Entrypoint
import os
from datetime import datetime, timedelta, timezone
from typing import Optional
from contextlib import asynccontextmanager
from dotenv import load_dotenv

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from sqlalchemy import Column, Integer, String, Boolean, DateTime

# Load environment variables
load_dotenv()
from passlib.context import CryptContext
from jose import jwt

from database import engine, Base, SessionLocal

# -------------------------------------------------------------------
# 1. Lifespan Event Handler (Startup / Shutdown)
# -------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        demo = db.query(UserModel).filter(UserModel.email == "supervisor@mocoss.my").first()
        if not demo:
            hashed = get_password_hash("password123")
            demo_user = UserModel(
                email="supervisor@mocoss.my",
                password_hash=hashed,
                full_name="Dr. Supervision Lead",
                role="supervisor"
            )
            db.add(demo_user)
            db.commit()
            print("[INFO] Demo user created: supervisor@mocoss.my / password123")
    except Exception as e:
        db.rollback()
        print(f"[WARNING] Error seeding demo user: {e}")
    finally:
        db.close()
        
    yield  # Application runs while suspended here
    
    # Shutdown logic (if needed in the future)

# -------------------------------------------------------------------
# 2. FastAPI App Initialization
# -------------------------------------------------------------------
app = FastAPI(
    title="MoCoSS Backend API",
    version="2.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------------------------------------------------
# 3. Security Configuration
# -------------------------------------------------------------------
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__ident="2b")
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))  # Default to 8 hours if not set

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
# 5. Helper Functions
# -------------------------------------------------------------------
def get_password_hash(password: str) -> str:
    password_bytes = password.encode('utf-8')[:72]
    return pwd_context.hash(password_bytes.decode('utf-8', errors='ignore'))

def verify_password(plain_password: str, hashed_password: str) -> bool:
    password_bytes = plain_password.encode('utf-8')[:72]
    return pwd_context.verify(password_bytes.decode('utf-8', errors='ignore'), hashed_password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(datetime.timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# -------------------------------------------------------------------
# 6. Include Modular Routers
# -------------------------------------------------------------------
from routes.system import router as system_router
from routes.auth import router as auth_router

app.include_router(system_router)
app.include_router(auth_router)