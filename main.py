# This is the Main FastAPI Application Entrypoint
import os
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine, Base, SessionLocal
from models.userM import UserModel, get_password_hash
from services.evaluationService import seed_default_criteria

load_dotenv()

# -------------------------------------------------------------------
# Lifespan Event Handler (Startup / Shutdown)
# -------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        demo = db.query(UserModel).filter(UserModel.email == "supervisor@mocoss.my").first()
        demo2 = db.query(UserModel).filter(UserModel.email == "f_supervisor@mocoss.my").first()
        demo3 = db.query(UserModel).filter(UserModel.email == "counselor@mocoss.my").first()
        hashed = get_password_hash("password123")
        hashed2 = get_password_hash("password456")
        hashed3 = get_password_hash("password789")

        if not demo:
            demo_user = UserModel(
                username="Test SV",
                email="supervisor@mocoss.my",
                hashed_password=hashed,
                full_name="Dr. Supervision Lead",
                role="supervisor"
            )
            db.add(demo_user)
            db.commit()
            print("[INFO] Demo user created: supervisor@mocoss.my / password123")
            
        else:
            demo.username = "Test SV"
            demo.password_hash = hashed
            demo.full_name = "Dr. Supervision Lead"
            demo.role = "supervisor"
            db.commit()
            print("[INFO] Demo user updated: supervisor@mocoss.my")
   
        if not demo2:
            demo_user2 = UserModel(
                username="Test FSV",
                email="f_supervisor@mocoss.my",
                hashed_password=hashed2,
                full_name="Dr. Feild Supervisor",
                role="field supervisor"
                )
            db.add(demo_user2)
            db.commit()
            print("[INFO] Demo user created: f_supervisor@mocoss.my / password456")
                    
        else:
            demo2.username = "Test FSV"
            demo2.password_hash = hashed2
            demo2.full_name = "Dr. Field Supervisor"
            demo2.role = "field supervisor"
            db.commit()
            print("[INFO] Demo user updated: f_supervisor@mocoss.my")
       
        
        if not demo3:
            demo_user3 = UserModel(
                username="Test COUN",
                email="counselor@mocoss.my",
                hashed_password=hashed3,
                full_name="UPSI Counselor",
                role="counselor"
                )
            db.add(demo_user3)
            db.commit()
            print("[INFO] Demo user created: counselor@mocoss.my / password789")
                        
        else:
            demo3.username = "Test COUN"
            demo3.password_hash = hashed3
            demo3.full_name = "UPSI Counselor"
            demo3.role = "counselor"
            db.commit()
            print("[INFO] Demo user updated: counselor@mocoss.my")
        seed_default_criteria(db)  # default grading rubric, only if the table is empty
    except Exception as e:
        db.rollback()
        print(f"[WARNING] Error seeding demo user: {e}")
    finally:
        db.close()
        
    yield  
    
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
from routes.grp_coun import router as grpcoun_router
from routes.case_anal import router as case_anal_router
from routes.log_book import router as log_book_router
from routes.ref_cons import router as ref_cons_router
from routes.self_reflection import router as self_reflection_router
from routes.psy_edu import router as psy_edu_router
from routes.prof_dev import router as prof_dev_router
from routes.full_mark import router as full_mark_router
from routes.adm_mgt import router as adm_mgt_router

app.include_router(system_router)
app.include_router(auth_router)
app.include_router(indcoun_router)
app.include_router(grpcoun_router)
app.include_router(case_anal_router)
app.include_router(log_book_router)
app.include_router(ref_cons_router)
app.include_router(self_reflection_router)
app.include_router(psy_edu_router)
app.include_router(prof_dev_router)
app.include_router(full_mark_router)
app.include_router(adm_mgt_router)

# Define storage directories
AUDIO_DIR = "uploadAudio"
VIDEO_DIR = "uploadVideo"

# Automatically create the directories if don't exist
os.makedirs(AUDIO_DIR, exist_ok=True)
os.makedirs(VIDEO_DIR, exist_ok=True)