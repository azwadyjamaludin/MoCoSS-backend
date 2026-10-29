from fastapi import APIRouter, Depends, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from database import get_db
from services.logBookService import create_log_entry, get_log_entries_by_user
from datetime import date

router = APIRouter(prefix="/log-book", tags=["Log Book"])

class LogBookCreateSchema(BaseModel):
    activity_title: str
    session_date: date
    duration_minutes: int = 60
    category: str = "Individual"
    reflection_notes: str = None

@router.post("/", status_code=status.HTTP_201_CREATED)
def create_log(data: LogBookCreateSchema, user_id: int = 1, db: Session = Depends(get_db)):
    record = create_log_entry(
        db, user_id, data.activity_title, data.session_date, 
        data.duration_minutes, data.category, data.reflection_notes
    )
    return {"status": "success", "data": record}

@router.get("/")
def list_logs(user_id: int = 1, db: Session = Depends(get_db)):
    records = get_log_entries_by_user(db, user_id)
    return {"status": "success", "data": records}