from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from database import get_db
from models.userM import UserModel
from services import aiService
from services.authService import get_current_user
from services.caseAnalService import create_case_analysis, get_case_analyses_by_user

router = APIRouter(prefix="/api/case-anal", tags=["Case Analysis"])

class CaseAnalysisCreateSchema(BaseModel):
    client_code: str
    presenting_problem: str
    session_dynamics: str

@router.post("/", status_code=status.HTTP_201_CREATED)
def create_analysis(data: CaseAnalysisCreateSchema, user_id: int = 1, db: Session = Depends(get_db)):
    # Note: user_id can later be extracted securely from current authenticated JWT user
    record = create_case_analysis(db, user_id, data.client_code, data.presenting_problem, data.session_dynamics)
    return {"status": "success", "data": record}

@router.get("/")
def list_analyses(user_id: int = 1, db: Session = Depends(get_db)):
    records = get_case_analyses_by_user(db, user_id)
    return {"status": "success", "data": records}


class AiDraftSchema(BaseModel):
    section: str                      # concern | background | assessment | formulation | plan | ethics
    case_ref: Optional[str] = None    # de-identified case code
    current_text: Optional[str] = None
    notes: List[str] = []             # optional text from linked sessions
    language: str = "EN"              # EN | BM


@router.post("/ai-draft")
def ai_draft(data: AiDraftSchema, user: UserModel = Depends(get_current_user)):
    """Draft one case-analysis section. The result is a draft the counselor must review."""
    aiService.check_rate_limit(user.id)
    try:
        result = aiService.draft_case_section(data.section, data.case_ref, data.current_text, data.notes, data.language)
    except aiService.AiError as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))
    return {"status": "success", "data": result}
