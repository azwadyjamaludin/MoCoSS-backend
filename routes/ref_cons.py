from fastapi import APIRouter, Depends, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from database import get_db
from services.refConsService import create_referral, get_referrals_by_user

router = APIRouter(prefix="/ref-cons", tags=["Referral Consultation"])

class ReferralCreateSchema(BaseModel):
    referred_to: str
    reason_for_referral: str
    case_summary: str = None

@router.post("/", status_code=status.HTTP_201_CREATED)
def create_consultation(data: ReferralCreateSchema, user_id: int = 1, db: Session = Depends(get_db)):
    record = create_referral(db, user_id, data.referred_to, data.reason_for_referral, data.case_summary)
    return {"status": "success", "data": record}

@router.get("/")
def list_consultations(user_id: int = 1, db: Session = Depends(get_db)):
    records = get_referrals_by_user(db, user_id)
    return {"status": "success", "data": records}