from sqlalchemy.orm import Session
from models.grpCoun import GrpCounSession

def create_grpcoun_record(
    db: Session, 
    client_name: str, 
    session_notes: str, 
    audio_file_path: str = None, 
    video_file_path: str = None
):

    # TODO: Replace mock feedback with actual Gemini AI processing logic in the future. For now, we use a placeholder string.
    ai_feedback_mock = "Gemini AI Supervision Feedback: The counselor demonstrated clear active listening and structured inquiry."

    """Creates a new GrpCoun session record in the database."""
    new_record = GrpCounSession(
        client_name=client_name,
        session_notes=session_notes,
        audio_file_path=audio_file_path,
        video_file_path=video_file_path,
        ai_feedback=ai_feedback_mock
    )
    db.add(new_record)
    db.commit()
    db.refresh(new_record)
    return new_record