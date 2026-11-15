from sqlalchemy import Column, ForeignKey, Index, Integer, String, Text, TIMESTAMP, text
from database import Base


class ReviewModel(Base):
    """One row per supervisor decision, so earlier rounds are kept when a record is returned and resubmitted."""
    __tablename__ = "reviews"
    __table_args__ = (Index("idx_review_target", "module", "record_id"),)

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    module = Column(String(30), nullable=False)       
    record_id = Column(Integer, nullable=False)
    reviewer_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    decision = Column(String(20), nullable=False)     
    comment = Column(Text, nullable=True)
    field_advice = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"))
