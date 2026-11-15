"""
routes/system.py - System and Health Check Routes
"""
from fastapi import APIRouter

router = APIRouter(prefix="/api/system",tags=["System"])


@router.get("/health")
async def health_check():
    """
    Backend health check endpoint.
    """
    return {
        "status": "online",
        "system": "MoCoSS Backend",
        "database": "MySQL (MacintoshHD2)"
    }