from sqlalchemy.orm import Session
from models.indCoun import IndCounSessionModel

def create_indcoun_record(
    db: Session, 
    client_name: str, 
    session_notes: str, 
    audio_url: str = None, 
    video_url: str = None
):

    # TODO: Replace mock feedback with actual Gemini AI processing logic in the future. For now, we use a placeholder string.
    ai_feedback_mock = "Gemini AI Supervision Feedback: The counselor demonstrated clear active listening and structured inquiry."

    """Creates a new IndCoun session record in the database."""
    new_record = IndCounSessionModel(
        client_name=client_name,
        session_notes=session_notes,
        audio_url=audio_url,
        video_url=video_url,
        ai_feedback=ai_feedback_mock
    )
    db.add(new_record)
    db.commit()
    db.refresh(new_record)
    return new_record