from sqlalchemy.orm import Session
from models.refCons import ReferralConsultationModel

def create_referral(db: Session, user_id: int, referred_to: str, reason_for_referral: str, case_summary: str):
    record = ReferralConsultationModel(
        user_id=user_id,
        referred_to=referred_to,
        reason_for_referral=reason_for_referral,
        case_summary=case_summary,
        status="Pending"
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record

def get_referrals_by_user(db: Session, user_id: int):
    return db.query(ReferralConsultationModel).filter(ReferralConsultationModel.user_id == user_id).all()