from sqlalchemy import Column, Integer, String, Text, DateTime
from datetime import datetime, timezone
from database import Base

class IndCounSessionModel(Base):
    __tablename__ = "indCoun_sessions"

    id = Column(Integer, primary_key=True, index=True)
    client_name = Column(String(150), nullable=False)
    session_notes = Column(Text, nullable=False)
    audio_url = Column(String(255), nullable=True)
    video_url = Column(String(255), nullable=True)
    ai_feedback = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))