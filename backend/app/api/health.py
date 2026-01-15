"""
健康檢查 API
"""
from fastapi import APIRouter, HTTPException
from app.core.redis import get_redis_client

router = APIRouter()


@router.get("/health")
async def health_check():
    """
    健康檢查端點
    檢查 API 和 Redis 連線狀態
    """
    try:
        # 檢查 Redis 連線
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
