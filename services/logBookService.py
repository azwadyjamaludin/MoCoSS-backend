from sqlalchemy.orm import Session
from models.logBook import LogBookModel
from datetime import date

def create_log_entry(db: Session, user_id: int, activity_title: str, session_date: date, duration_minutes: int, category: str, reflection_notes: str):
    record = LogBookModel(
        user_id=user_id,
        activity_title=activity_title,
        session_date=session_date,
        duration_minutes=duration_minutes,
        category=category,
        reflection_notes=reflection_notes
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record

def get_log_entries_by_user(db: Session, user_id: int):
    return db.query(LogBookModel).filter(LogBookModel.user_id == user_id).all()