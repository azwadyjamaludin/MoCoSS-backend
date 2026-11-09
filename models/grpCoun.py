from sqlalchemy import Column, Integer, String, Text, ForeignKey, TIMESTAMP, text
from database import Base

class GrpCounSession(Base):
    __tablename__ = "grpCoun_sessions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    group_name = Column(String(150), nullable=True)
    participant_count = Column(Integer, default=0)
    audio_file_path = Column(String(500), nullable=True)
    video_file_path = Column(String(500), nullable=True)
    session_notes = Column(Text, nullable=True)
    transcript = Column(Text, nullable=True)
    ai_feedback = Column(Text, nullable=True)
    sv_feedback = Column(Text, nullable=True)
    client_status = Column(String(255), nullable=True)
    duration_minutes = Column(Integer, nullable=True)
    consent_given = Column(Integer, default=0)
    ai_status = Column(String(50), default="Pending")
    ai_error = Column(String(255), nullable=True)
    ai_gerated_at = Column(TIMESTAMP, nullable=True)
    ai_model = Column(String(100), nullable=True)
    ai_prompt_version = Column(String(20), nullable=True)  
    created_at = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"))
    updated_at = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"))

   