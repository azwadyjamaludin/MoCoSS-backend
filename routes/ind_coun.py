import os
import shutil
from fastapi import APIRouter, Depends, status, Form, File, UploadFile
from pydantic import BaseModel
from sqlalchemy.orm import Session
from database import get_db
from services.indCounService import create_indcoun_record

VIDEO_DIR = os.path.join(os.path.dirname(__file__), "videos")
AUDIO_DIR = os.path.join(os.path.dirname(__file__), "audio")

router = APIRouter(
    prefix="/api/indCoun",
    tags=["Individual Counseling"]
)

class IndcounCreateSchema(BaseModel):
    client_name: str
    session_notes: str
    audio_url: str = None
    video_url: str = None
    ai_feedback: str = None

@router.post("/sessions", status_code=status.HTTP_201_CREATED)
def create_session(
    data: IndcounCreateSchema, 
    client_name: str = Form(...),
    session_notes: str = Form(...),
    audio_file: UploadFile = File(None),
    video_file: UploadFile = File(None),
    ai_feedback: str = Form(...),
    db: Session = Depends(get_db)):

    video_url = None
    
    if video_file:
        # Define where to save the physical file locally
        os.makedirs(VIDEO_DIR, exist_ok=True)
        file_path = os.path.join(VIDEO_DIR, video_file.filename)
        
        # Save the physical file to disk
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(video_file.file, buffer)
            
        # Create the URL/path reference
        video_url = f"/{file_path}"

    audio_url = None  

    if audio_file:
        # Define where to save the physical file locally
        os.makedirs(AUDIO_DIR, exist_ok=True)
        file_path = os.path.join(AUDIO_DIR, audio_file.filename)
        
        # Save the physical file to disk
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(audio_file.file, buffer)
            
        # Create the URL/path reference
        audio_url = f"/{file_path}"

    if ai_feedback:
        # If AI feedback is provided, use it directly
        ai_feedback = ai_feedback

    """
    Save an individual counseling session (with optional audio/video recordings) 
    and generate Gemini AI supervision feedback.
    """
    new_session = create_indcoun_record(
        client_name=client_name,
        session_notes=session_notes,
        audio_url=audio_url,
        video_url=video_url,
        ai_feedback=ai_feedback
    )
    
    return {
        "status": "success",
        "message": "Counseling session saved and processed successfully",
        "data": {
            "id": new_session.id,
            "client_name": new_session.client_name,
            "session_notes": new_session.session_notes,
            "audio_url": new_session.audio_url,
            "video_url": new_session.video_url,
            "ai_feedback": new_session.ai_feedback,
            "created_at": new_session.created_at
        }
    }