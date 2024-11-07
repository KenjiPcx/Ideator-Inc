from fastapi import APIRouter
from datetime import datetime

health_router = APIRouter(prefix="/health", tags=["Health"])

@health_router.get("")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "ideabot",
        "version": "1.0.0"  # You can make this dynamic based on your version
    }