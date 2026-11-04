from sqlalchemy import Boolean, Column, Integer, String, TIMESTAMP


class AiSessionColumns:
    client_status = Column(String(255), nullable=True)
    duration_minutes = Column(Integer, nullable=True)
    consent_given = Column(Boolean, default=False)
    ai_status = Column(String(20), default="none")
    ai_error = Column(String(255), nullable=True)
    ai_generated_at = Column(TIMESTAMP, nullable=True)
    ai_model = Column(String(100), nullable=True)
    ai_prompt_version = Column(String(20), nullable=True)
