from sqlalchemy import Column, Integer, String, Text, Date, TIMESTAMP, ForeignKey, text
from database import Base


class SelfReflectionModel(Base):
    __tablename__ = "self_reflections"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    reflection_date = Column(Date, nullable=False)
    content = Column(Text, nullable=False)          # what happened / how I felt
    strengths = Column(Text, nullable=True)
    growth_areas = Column(Text, nullable=True)
    action_plan = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"))
    updated_at = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"))
