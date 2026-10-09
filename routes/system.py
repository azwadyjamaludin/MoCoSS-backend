"""
routes/system.py - System and Health Check Routes
"""
from fastapi import APIRouter

router = APIRouter(prefix="/api/system",tags=["System"])

# @router.get("/")
#def read_root():
#    """Health check endpoint to verify API availability."""
#    return {"message": "MoCoSS Backend API is running successfully!"}

@router.get("/health")
async def health_check():
    """
    Health check endpoint to verify backend connectivity.
    """
    return {
        "status": "online",
        "system": "MoCoSS Backend",
        "database": "MySQL (MicroSD)"
    }