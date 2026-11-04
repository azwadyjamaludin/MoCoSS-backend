import json
import logging
import os
import uuid
from datetime import date, datetime
from typing import Optional

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from database import SessionLocal
from services import aiService

log = logging.getLogger("mocoss.sessions")

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AUDIO_DIR = os.path.join(PROJECT_ROOT, "uploadAudio")
VIDEO_DIR = os.path.join(PROJECT_ROOT, "uploadVideo")
AUDIO_EXT = {".m4a", ".mp3", ".wav", ".aac", ".ogg", ".flac", ".caf"}
VIDEO_EXT = {".mp4", ".mov", ".m4v"}
MAX_UPLOAD_MB = int(os.getenv("MAX_UPLOAD_MB", "300"))


def save_upload(upload: Optional[UploadFile], directory: str, allowed: set) -> Optional[str]:
    """Save an upload under a random name (never the client's filename) and return its path relative to the project.

    Recordings are not served by any public URL. Only the server reads them.
    """
    if upload is None or not upload.filename:
        return None
    ext = os.path.splitext(upload.filename)[1].lower()
    if ext not in allowed:
        raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail=f"File type {ext or '?'} is not supported.")

    os.makedirs(directory, exist_ok=True)
    path = os.path.join(directory, f"{uuid.uuid4().hex}{ext}")
    limit = MAX_UPLOAD_MB * 1024 * 1024
    written = 0
    try:
        with open(path, "wb") as out:
            while chunk := upload.file.read(1024 * 1024):
                written += len(chunk)
                if written > limit:
                    raise HTTPException(status_code=413, detail=f"File is larger than {MAX_UPLOAD_MB} MB.")
                out.write(chunk)
    except Exception:
        if os.path.exists(path):
            os.remove(path)
        raise
    if written == 0:
        os.remove(path)
        return None
    return os.path.relpath(path, PROJECT_ROOT)


def remove_quietly(relative_path: Optional[str]) -> None:
    if relative_path:
        try:
            os.remove(os.path.join(PROJECT_ROOT, relative_path))
        except OSError:
            pass


def create_session(
    db: Session, Model, user_id: int, kind: str, code_attr: str, case_code: str, session_notes: str,
    client_status: str, duration_hours: float, audio_path: Optional[str], video_path: Optional[str],
):
    has_media = bool(audio_path or video_path)
    ai_status, ai_error = ("pending", None) if has_media else ("none", None)
    if has_media:
        try:
            aiService.check_rate_limit(user_id)
        except HTTPException:
            ai_status, ai_error = "skipped", "AI request limit reached. Try again later."

    record = Model(
        user_id=user_id,
        title=f"{kind.capitalize()} session {date.today().isoformat()}",
        session_notes=session_notes or None,
        client_status=client_status or None,
        duration_minutes=int(round(duration_hours * 60)) if duration_hours else None,
        consent_given=True,
        audio_file_path=audio_path,
        video_file_path=video_path,
        ai_status=ai_status,
        ai_error=ai_error,
        **{code_attr: case_code},
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def get_session(db: Session, Model, user_id: int, session_id: int):
    record = db.query(Model).filter(Model.id == session_id, Model.user_id == user_id).first()
    if record is None:
        raise HTTPException(status_code=404, detail="Session not found.")
    return record


def list_sessions(db: Session, Model, user_id: int):
    return db.query(Model).filter(Model.user_id == user_id).order_by(Model.id.desc()).all()


def present(record, code_attr: str) -> dict:
    feedback = None
    if record.ai_feedback:
        try:
            feedback = json.loads(record.ai_feedback)
        except json.JSONDecodeError:  # older rows hold plain text
            feedback = {"summary": record.ai_feedback, "strengths": [], "areas_to_improve": [],
                        "skills_observed": [], "ethical_flags": [], "questions_for_supervision": [], "is_mock": False}
    return {
        "id": record.id,
        "title": record.title,
        "case_code": getattr(record, code_attr),
        "client_status": record.client_status,
        "session_notes": record.session_notes,
        "duration_minutes": record.duration_minutes,
        "has_audio": bool(record.audio_file_path),
        "has_video": bool(record.video_file_path),
        "ai_status": record.ai_status or "none",
        "ai_error": record.ai_error,
        "ai_generated_at": record.ai_generated_at.isoformat() if record.ai_generated_at else None,
        "ai_feedback": feedback,
        "transcript": record.transcript,
        "created_at": record.created_at.isoformat() if record.created_at else None,
    }


def run_session_analysis(Model, session_id: int, kind: str, language: str) -> None:
    """Runs after the upload response was sent. Uses its own DB session because the request's is closed by then."""
    db = SessionLocal()
    try:
        record = db.get(Model, session_id)
        if record is None or record.ai_status != "pending":
            return
        record.ai_status = "processing"
        db.commit()

        media = record.audio_file_path or record.video_file_path
        result = aiService.analyze_session(os.path.join(PROJECT_ROOT, media), record.session_notes, kind, language)

        record.transcript = result["transcript"] or None
        record.ai_feedback = json.dumps(result["feedback"], ensure_ascii=False)
        record.ai_model = result["model"]
        record.ai_prompt_version = result["prompt_version"]
        record.ai_generated_at = datetime.utcnow()
        record.ai_status, record.ai_error = "done", None
        db.commit()
    except aiService.AiError as e:
        _mark_failed(db, Model, session_id, str(e))
    except Exception:
        log.exception("AI analysis crashed for %s %s", Model.__name__, session_id)
        _mark_failed(db, Model, session_id, "Something went wrong while generating feedback.")
    finally:
        db.close()


def _mark_failed(db: Session, Model, session_id: int, message: str) -> None:
    db.rollback()
    record = db.get(Model, session_id)
    if record is not None:
        record.ai_status, record.ai_error = "failed", message[:255]
        db.commit()
