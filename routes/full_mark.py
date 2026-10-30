from typing import List, Optional

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db
from models.userM import UserModel
from services.authService import SUPERVISOR_ROLES, get_current_user, require_roles
from services.evaluationService import (
    create_evaluation, get_evaluation, list_criteria, list_evaluations, list_supervisees,
)
from services.serializeUtil import to_dict

router = APIRouter(prefix="/api/full-mark", tags=["Full Mark Evaluation"])


class ScoreSchema(BaseModel):
    criterion_id: int
    marks: float
    remarks: Optional[str] = None


class EvaluationCreateSchema(BaseModel):
    supervisee_id: int
    comments: Optional[str] = None
    scores: List[ScoreSchema]


@router.get("/criteria")
def get_rubric(user: UserModel = Depends(get_current_user), db: Session = Depends(get_db)):
    return {"status": "success", "data": [to_dict(c) for c in list_criteria(db)]}


@router.get("/supervisees")
def get_supervisees(
    user: UserModel = Depends(require_roles("admin", *SUPERVISOR_ROLES)), db: Session = Depends(get_db)
):
    data = [{"id": u.id, "full_name": u.full_name, "email": u.email} for u in list_supervisees(db, user)]
    return {"status": "success", "data": data}


@router.get("/evaluations")
def get_evaluations(user: UserModel = Depends(get_current_user), db: Session = Depends(get_db)):
    return {"status": "success", "data": list_evaluations(db, user)}


@router.get("/evaluations/{evaluation_id}")
def get_one_evaluation(evaluation_id: int, user: UserModel = Depends(get_current_user), db: Session = Depends(get_db)):
    return {"status": "success", "data": get_evaluation(db, user, evaluation_id)}


@router.post("/evaluations", status_code=status.HTTP_201_CREATED)
def submit_evaluation(
    data: EvaluationCreateSchema,
    user: UserModel = Depends(require_roles(*SUPERVISOR_ROLES)),
    db: Session = Depends(get_db),
):
    scores = [s.model_dump() if hasattr(s, "model_dump") else s.dict() for s in data.scores]
    evaluation = create_evaluation(db, user, data.supervisee_id, data.comments, scores)
    return {"status": "success", "data": get_evaluation(db, user, evaluation.id)}
