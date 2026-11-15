from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from database import get_db
from models.userM import UserModel
from services import aiService
from services.authService import get_current_user
from services import reviewService as review

router = APIRouter(prefix="/api/case-anal", tags=["Case Analysis"])
MODULE = "case-anal"

class CaseAnalysisSchema(BaseModel):
    client_code: str
    presenting_problem: str
    session_dynamics: Optional[str] = None
    sections: Optional[str] = None  # JSON text
    submit: bool = False  


def _data(body: CaseAnalysisSchema) -> dict:
    return body.model_dump(exclude={"submit"}) if hasattr(body, "model_dump") else body.dict(exclude={"submit"})


@router.post("/", status_code=status.HTTP_201_CREATED)
def create_analysis(body: CaseAnalysisSchema, user: UserModel = Depends(get_current_user), db: Session = Depends(get_db)):
    return {"status": "success", "data": review.create_own(db, MODULE, user, _data(body), body.submit)}


@router.get("/")
def list_analyses(user: UserModel = Depends(get_current_user), db: Session = Depends(get_db)):
    return {"status": "success", "data": review.list_own(db, MODULE, user)}


@router.get("/{record_id}")
def get_analysis(record_id: int, user: UserModel = Depends(get_current_user), db: Session = Depends(get_db)):
    return {"status": "success", "data": review.get_own(db, MODULE, user, record_id)}


@router.put("/{record_id}")
def update_analysis(record_id: int, body: CaseAnalysisSchema, user: UserModel = Depends(get_current_user), db: Session = Depends(get_db)):
    """Only a draft or a returned record can be edited."""
    return {"status": "success", "data": review.update_own(db, MODULE, user, record_id, _data(body), body.submit)}


class AiDraftSchema(BaseModel):
    section: str                      
    case_ref: Optional[str] = None    
    current_text: Optional[str] = None
    notes: List[str] = []             
    language: str = "EN"              


@router.post("/ai-draft")
def ai_draft(data: AiDraftSchema, user: UserModel = Depends(get_current_user)):
    """Draft one case-analysis section. The result is a draft the counselor must review."""
    aiService.check_rate_limit(user.id)
    try:
        result = aiService.draft_case_section(data.section, data.case_ref, data.current_text, data.notes, data.language)
    except aiService.AiError as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))
    return {"status": "success", "data": result}
