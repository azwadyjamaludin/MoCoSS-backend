from sqlalchemy import Column, Integer, String, Text, TIMESTAMP, ForeignKey, text
from database import Base

class CaseAnalysisModel(Base):
    __tablename__ = "case_analyses"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    client_code = Column(String(100), nullable=False)  # Anonymized client identifier
    presenting_problem = Column(Text, nullable=False)
    session_dynamics = Column(Text, nullable=True)
    ai_supervision_feedback = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"))
    updated_at = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"))