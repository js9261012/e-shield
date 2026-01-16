"""
健康檢查 API
"""
from fastapi import APIRouter, HTTPException
from app.core.redis import get_redis_client

router = APIRouter()


@router.get("/health")
async def health_check():
    """健康檢查端點"""
    try:
        redis_client = get_redis_client()
        redis_client.ping()
        
        return {
            "status": "healthy",
            "redis": "connected"
        }
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Service unhealthy: {str(e)}"
        )
