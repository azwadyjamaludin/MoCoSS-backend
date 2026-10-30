from sqlalchemy import Column, Integer, String, Text, Date, TIMESTAMP, ForeignKey, text
from database import Base


class PsychoEducationModel(Base):
    __tablename__ = "psychoeducation_activities"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    topic = Column(String(255), nullable=True)            # e.g. stress management
    target_group = Column(String(150), nullable=True)     # e.g. Form 4 students
    delivery_method = Column(String(50), default="Workshop")  # Workshop, Talk, Module, Handout, Online
    activity_date = Column(Date, nullable=False)
    participant_count = Column(Integer, default=0)
    materials_notes = Column(Text, nullable=True)         # materials / module used
    outcome_notes = Column(Text, nullable=True)           # outcome and feedback
    created_at = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"))
    updated_at = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"))
