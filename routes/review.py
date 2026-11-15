from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db
from models.userM import UserModel
from services import reviewService as svc
from services.authService import SUPERVISOR_ROLES, get_current_user, require_roles

router = APIRouter(prefix="/api/review", tags=["Review"])


class DecisionSchema(BaseModel):
    decision: str                        
    comment: Optional[str] = None        
    field_advice: Optional[str] = None   


@router.get("/queue")
def review_queue(
    status: str = "submitted", module: Optional[str] = None,
    user: UserModel = Depends(require_roles(*SUPERVISOR_ROLES)), db: Session = Depends(get_db),
):
    """Submitted work from your assigned counselors, across all modules. status: submitted | approved | returned | all."""
    return {"status": "success", "data": svc.queue(db, user, status, module)}


@router.get("/{module}/{record_id}")
def review_detail(
    module: str, record_id: int,
    user: UserModel = Depends(require_roles(*SUPERVISOR_ROLES)), db: Session = Depends(get_db),
):
    return {"status": "success", "data": svc.get_for_review(db, user, module, record_id)}


@router.post("/{module}/{record_id}/decision")
def review_decision(
    module: str, record_id: int, data: DecisionSchema,
    user: UserModel = Depends(require_roles(*SUPERVISOR_ROLES)), db: Session = Depends(get_db),
):
    return {"status": "success", "data": svc.decide(db, user, module, record_id, data.decision, data.comment, data.field_advice)}


@router.post("/{module}/{record_id}/submit")
def submit_for_review(
    module: str, record_id: int,
    user: UserModel = Depends(get_current_user), db: Session = Depends(get_db),
):
    return {"status": "success", "data": svc.submit_own(db, module, user, record_id)}
