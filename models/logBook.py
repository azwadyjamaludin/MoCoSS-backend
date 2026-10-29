from sqlalchemy import Column, Integer, String, Text, Date, TIMESTAMP, ForeignKey, text
from database import Base

class LogBookModel(Base):
    __tablename__ = "log_books"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    activity_title = Column(String(255), nullable=False)
    session_date = Column(Date, nullable=False)
    duration_minutes = Column(Integer, default=60)
    category = Column(String(50), default="Individual")  # Individual, Group, Consultation, etc.
    reflection_notes = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"))
    updated_at = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"))