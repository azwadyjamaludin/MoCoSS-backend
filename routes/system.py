"""
routes/system.py - System and Health Check Routes
"""
from fastapi import APIRouter

router = APIRouter(tags=["System"])

@router.get("/")
def read_root():
    """Health check endpoint to verify API availability."""
    return {"message": "MoCoSS Backend API is running successfully!"}