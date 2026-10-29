from fastapi import APIRouter, Depends, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from database import get_db
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