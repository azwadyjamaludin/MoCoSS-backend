from sqlalchemy import Column, Integer, String, Text, TIMESTAMP, ForeignKey, text
from database import Base

class ReferralConsultationModel(Base):
    __tablename__ = "referral_consultations"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    referred_to = Column(String(150), nullable=False)  # Name of specialist, agency, or supervisor
    reason_for_referral = Column(Text, nullable=False)
    case_summary = Column(Text, nullable=True)
    status = Column(String(50), default="Pending")  # Pending, In Progress, Completed
    recommendations = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"))
    updated_at = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"))