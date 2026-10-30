from sqlalchemy import (Boolean, Column, ForeignKey, Integer, Numeric, String, Text, TIMESTAMP, UniqueConstraint, text,)
from database import Base

class EvaluationCriterionModel(Base):
    """One row of the grading rubric. Managed by admins."""
    __tablename__ = "evaluation_criteria"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(150), nullable=False)
    description = Column(Text, nullable=True)
    max_marks = Column(Integer, nullable=False, default=10)
    sort_order = Column(Integer, nullable=False, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"))
    updated_at = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"))


class EvaluationModel(Base):
    """One evaluation of a supervisee (counselor) by a supervisor."""
    __tablename__ = "evaluations"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    supervisee_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    evaluator_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    total_marks = Column(Numeric(7, 2), nullable=False, default=0)
    max_total = Column(Numeric(7, 2), nullable=False, default=0)
    comments = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"))
    updated_at = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"))


class EvaluationScoreModel(Base):
    __tablename__ = "evaluation_scores"
    __table_args__ = (UniqueConstraint("evaluation_id", "criterion_id", name="uq_eval_criterion"),)

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    evaluation_id = Column(Integer, ForeignKey("evaluations.id", ondelete="CASCADE"), nullable=False, index=True)
    criterion_id = Column(Integer, ForeignKey("evaluation_criteria.id", ondelete="RESTRICT"), nullable=False)
    marks = Column(Numeric(6, 2), nullable=False)
    remarks = Column(Text, nullable=True)
