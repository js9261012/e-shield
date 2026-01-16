"""
速率限制中間件
"""
from fastapi import Request, HTTPException
from app.core.redis import get_redis_client
from typing import Optional
import time


class RateLimiter:
    """速率限制器"""
    
    def __init__(self, max_requests: int = 10, window_seconds: int = 60):
        """
        初始化速率限制器
        
        Args:
            max_requests: 時間窗口內最大請求數
            window_seconds: 時間窗口（秒）
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
    
    def _get_client_ip(self, request: Request) -> str:
        """取得客戶端 IP"""
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        if request.client:
            return request.client.host
        
        return "unknown"
    
    def _get_rate_limit_key(self, ip: str, endpoint: str) -> str:
        """取得速率限制 Redis key"""
        return f"rate_limit:{ip}:{endpoint}"
    
    async def check_rate_limit(self, request: Request, endpoint: str = "default") -> bool:
        """
        檢查速率限制
        
        Args:
            request: FastAPI Request 物件
            endpoint: 端點名稱（用於區分不同端點的速率限制）
            
        Returns:
            bool: True 表示通過，False 表示超過限制
            
        Raises:
            HTTPException: 超過速率限制時拋出 429 錯誤
        """
        client_ip = self._get_client_ip(request)
        redis_client = get_redis_client()
        rate_limit_key = self._get_rate_limit_key(client_ip, endpoint)
        
        current_time = int(time.time())
        window_start = current_time - self.window_seconds
        
        redis_client.zremrangebyscore(rate_limit_key, 0, window_start)
        current_count = redis_client.zcard(rate_limit_key)
        
        if current_count >= self.max_requests:
            raise HTTPException(
                status_code=429,
                detail={
                    "error": "RATE_LIMIT_EXCEEDED",
                    "message": f"請求過於頻繁，請在 {self.window_seconds} 秒後再試",
                    "retry_after": self.window_seconds
                }
            )
        
        redis_client.zadd(rate_limit_key, {str(current_time): current_time})
        redis_client.expire(rate_limit_key, self.window_seconds)
        
        return True


default_rate_limiter = RateLimiter(max_requests=10, window_seconds=60)
queue_rate_limiter = RateLimiter(max_requests=20, window_seconds=60)
