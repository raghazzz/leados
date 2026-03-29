from fastapi import APIRouter
from datetime import datetime

router = APIRouter()

# When someone visits /api/v1/health it returns this
@router.get("/health")
async def health():
    return {
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "LeadOS API"
    }