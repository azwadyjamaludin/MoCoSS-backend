from sqlalchemy import Column, Integer, String, Text, TIMESTAMP


class ReviewColumns:
    """Submission and review state, mixed into every module the supervisor can review.

    status: draft -> submitted -> approved | returned (a returned record can be edited and submitted again)
    """
    status = Column(String(20), nullable=False, default="draft", server_default="draft", index=True)
    submitted_at = Column(TIMESTAMP, nullable=True)
    reviewed_at = Column(TIMESTAMP, nullable=True)
    reviewed_by = Column(Integer, nullable=True)  
    review_comment = Column(Text, nullable=True)
    field_advice = Column(Text, nullable=True)    
