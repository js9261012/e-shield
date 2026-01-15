"""
Redis 連線模組
"""
import os
from typing import Optional
import redis
from redis.connection import ConnectionPool

# Redis 連線池
_redis_pool: Optional[ConnectionPool] = None
_redis_client: Optional[redis.Redis] = None


def get_redis_url() -> str:
    """取得 Redis URL，從環境變數或使用預設值"""
    return os.getenv("REDIS_URL", "redis://localhost:6379")


def get_redis_client() -> redis.Redis:
    """
    取得 Redis 客戶端（單例模式）
    
    Returns:
        redis.Redis: Redis 客戶端實例
    """
    global _redis_client, _redis_pool
    
    if _redis_client is None:
        redis_url = get_redis_url()
        _redis_pool = ConnectionPool.from_url(redis_url, decode_responses=True)
        _redis_client = redis.Redis(connection_pool=_redis_pool)
    
    return _redis_client


def close_redis():
    """關閉 Redis 連線"""
    global _redis_client, _redis_pool
    
    if _redis_client:
        _redis_client.close()
        _redis_client = None
    
    if _redis_pool:
        _redis_pool.disconnect()
        _redis_pool = None
