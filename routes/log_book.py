from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db
from models.userM import UserModel
from services import reviewService as svc
from services.authService import get_current_user

router = APIRouter(prefix="/api/log-book", tags=["Log Book"])
MODULE = "log-book"


class LogBookSchema(BaseModel):
    activity_title: str
    session_date: date
    duration_minutes: int = 60
    category: str = "Individual"
    reflection_notes: Optional[str] = None
    submit: bool = False  


def _data(body: LogBookSchema) -> dict:
    return body.model_dump(exclude={"submit"}) if hasattr(body, "model_dump") else body.dict(exclude={"submit"})


@router.post("/", status_code=status.HTTP_201_CREATED)
def create_log(body: LogBookSchema, user: UserModel = Depends(get_current_user), db: Session = Depends(get_db)):
    return {"status": "success", "data": svc.create_own(db, MODULE, user, _data(body), body.submit)}


@router.get("/")
def list_logs(user: UserModel = Depends(get_current_user), db: Session = Depends(get_db)):
    return {"status": "success", "data": svc.list_own(db, MODULE, user)}


@router.get("/{record_id}")
def get_log(record_id: int, user: UserModel = Depends(get_current_user), db: Session = Depends(get_db)):
    return {"status": "success", "data": svc.get_own(db, MODULE, user, record_id)}


@router.put("/{record_id}")
def update_log(record_id: int, body: LogBookSchema, user: UserModel = Depends(get_current_user), db: Session = Depends(get_db)):
    return {"status": "success", "data": svc.update_own(db, MODULE, user, record_id, _data(body), body.submit)}
