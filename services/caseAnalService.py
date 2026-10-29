from sqlalchemy.orm import Session
from models.caseAnal import CaseAnalysisModel

def create_case_analysis(db: Session, user_id: int, client_code: str, presenting_problem: str, session_dynamics: str):
    # TODO: Integrate Gemini AI feedback generation here
    ai_feedback = "AI Supervision Feedback: The counselor demonstrated strong empathy and structured probing."
    
    record = CaseAnalysisModel(
        user_id=user_id,
        client_code=client_code,
        presenting_problem=presenting_problem,
        session_dynamics=session_dynamics,
        ai_supervision_feedback=ai_feedback
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record

def get_case_analyses_by_user(db: Session, user_id: int):
    return db.query(CaseAnalysisModel).filter(CaseAnalysisModel.user_id == user_id).all()