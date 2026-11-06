from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from database import get_db
from models.userM import UserModel
from services import counselingSessionService as svc
from services.authService import get_current_user


def build_session_router(prefix: str, tag: str, Model, kind: str, code_attr: str) -> APIRouter:
    
    router = APIRouter(prefix=prefix, tags=[tag])

    @router.post("/sessions", status_code=status.HTTP_201_CREATED)
    def create_session(
        background_tasks: BackgroundTasks,
        case_code: str = Form(...),
        session_notes: str = Form(""),
        client_status: str = Form(""),
        duration_hours: float = Form(0),
        consent: bool = Form(False),
        language: str = Form("EN"),
        audio: Optional[UploadFile] = File(None),
        video: Optional[UploadFile] = File(None),
        user: UserModel = Depends(get_current_user),
        db: Session = Depends(get_db),
    ):
        case_code = case_code.strip()
        if not case_code or len(case_code) > 100:
            raise HTTPException(status_code=422, detail="A case code is required (100 characters at most).")
        if not consent:
            raise HTTPException(status_code=422, detail="Client consent to the recording must be confirmed.")
        if duration_hours < 0:
            raise HTTPException(status_code=422, detail="Duration cannot be negative.")

        audio_path = svc.save_upload(audio, svc.AUDIO_DIR, svc.AUDIO_EXT)
        try:
            video_path = svc.save_upload(video, svc.VIDEO_DIR, svc.VIDEO_EXT)
        except Exception:
            svc.remove_quietly(audio_path)
            raise

        record = svc.create_session(
            db, Model, user.id, kind, code_attr, case_code, session_notes, client_status.strip(),
            duration_hours, audio_path, video_path,
        )
        if record.ai_status == "pending":
            background_tasks.add_task(svc.run_session_analysis, Model, record.id, kind, language)
        return {"status": "success", "data": svc.present(record, code_attr)}

    @router.get("/sessions")
    def list_sessions(user: UserModel = Depends(get_current_user), db: Session = Depends(get_db)):
        return {"status": "success", "data": [svc.present(r, code_attr) for r in svc.list_sessions(db, Model, user.id)]}

    @router.get("/sessions/{session_id}")
    def get_session(session_id: int, user: UserModel = Depends(get_current_user), db: Session = Depends(get_db)):
        return {"status": "success", "data": svc.present(svc.get_session(db, Model, user.id, session_id), code_attr)}

    return router
