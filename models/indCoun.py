from sqlalchemy import Column, Integer, String, Text, ForeignKey, TIMESTAMP, text
from database import Base

class IndCounSession(Base):
    __tablename__ = "indCoun_sessions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    client_identifier = Column(String(100), nullable=True)
    audio_file_path = Column(String(500), nullable=True)
    video_file_path = Column(String(500), nullable=True)
    session_notes = Column(Text, nullable=True)
    transcript = Column(Text, nullable=True)
    ai_feedback = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"))
    updated_at = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"))

    