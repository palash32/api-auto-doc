"""
Health check routes
"""

from fastapi import APIRouter
from datetime import datetime
import time

router = APIRouter()
start_time = time.time()


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": "2.0.0",
        "service": "ai",
        "timestamp": datetime.now().isoformat(),
        "uptime_seconds": round(time.time() - start_time, 2)
    }


@router.get("/health/ready")
async def ready_check():
    """Readiness probe for Kubernetes."""
    return {"ready": True}


@router.get("/health/live")
async def live_check():
    """Liveness probe for Kubernetes."""
    return {"live": True}
