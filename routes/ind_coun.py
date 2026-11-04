from models.indCoun import IndCounSession
from routes.counseling_router import build_session_router

router = build_session_router(
    "/api/indCoun", "Individual Counseling", IndCounSession, kind="individual", code_attr="client_identifier"
)
