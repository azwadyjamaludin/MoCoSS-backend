from sqlalchemy import Column, ForeignKey, Integer, TIMESTAMP, UniqueConstraint, text
from database import Base


class SupervisorAssignmentModel(Base):
    """Links a supervisee (counselor) to the supervisor who evaluates them."""
    __tablename__ = "supervisor_assignments"
    __table_args__ = (UniqueConstraint("supervisor_id", "supervisee_id", name="uq_supervisor_supervisee"),)

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    supervisor_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    supervisee_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"))
