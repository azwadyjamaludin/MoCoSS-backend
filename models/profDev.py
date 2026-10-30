from sqlalchemy import Column, Integer, String, Text, Date, Numeric, TIMESTAMP, ForeignKey, text
from database import Base


class ProfDevModel(Base):
    __tablename__ = "professional_developments"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    activity_title = Column(String(255), nullable=False)
    activity_type = Column(String(50), default="Workshop")  # Workshop, Seminar, Course, Conference, Webinar, Other
    provider = Column(String(150), nullable=True)
    activity_date = Column(Date, nullable=False)
    hours = Column(Numeric(5, 2), default=0)
    certificate_ref = Column(String(150), nullable=True)
    learning_outcome = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"))
    updated_at = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"))
