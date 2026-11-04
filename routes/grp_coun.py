from models.grpCoun import GrpCounSession
from routes.counseling_router import build_session_router

router = build_session_router(
    "/api/grpCoun", "Group Counseling", GrpCounSession, kind="group", code_attr="group_name"
)
