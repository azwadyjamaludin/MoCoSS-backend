# This is the Main FastAPI Application Entrypoint
import os
from contextlib import asynccontextmanager
from dotenv import load_dotenv

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Load environment variables
load_dotenv()
from database import engine, Base, SessionLocal
from models.userM import UserModel, get_password_hash

# -------------------------------------------------------------------
# Lifespan Event Handler (Startup / Shutdown)
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
            
        else:
            demo.password_hash = hashed
            demo.full_name = "Dr. Supervision Lead"
            demo.role = "supervisor"
            db.commit()
            print("[INFO] Demo user updated: supervisor@mocoss.my")
    except Exception as e:
        db.rollback()
        print(f"[WARNING] Error seeding demo user: {e}")
    finally:
        db.close()
        
    yield  # Application runs while suspended here
    
    # Shutdown logic (if needed in the future)

# -------------------------------------------------------------------
# FastAPI App Initialization
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
# Include Modular Routers
# -------------------------------------------------------------------
from routes.system import router as system_router
from routes.auth import router as auth_router
from routes.ind_coun import router as indcoun_router

app.include_router(system_router)
app.include_router(auth_router)
app.include_router(indcoun_router)

# Define storage directories
AUDIO_DIR = "uploadAudio"
VIDEO_DIR = "uploadVideo"

# Automatically create the directories if don't exist
os.makedirs(AUDIO_DIR, exist_ok=True)
os.makedirs(VIDEO_DIR, exist_ok=True)