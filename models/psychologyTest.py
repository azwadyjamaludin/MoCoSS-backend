from sqlalchemy import Column, Integer, String, Text, Date, Numeric, TIMESTAMP, ForeignKey, text
from database import Base


class PsychologyTestModel(Base):
    """A record of a psychological test given by the counselor. Stores a case code, never a client name."""
    __tablename__ = "psychology_tests"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    test_name = Column(String(150), nullable=False)       # e.g. DASS-21
    case_ref = Column(String(100), nullable=True)         # de-identified case code, e.g. C-014
    test_date = Column(Date, nullable=False)
    raw_score = Column(Numeric(7, 2), nullable=True)
    interpretation = Column(String(255), nullable=True)   # e.g. moderate anxiety
    notes = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"))
    updated_at = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"))
