"""
Pytest 配置和共用 fixtures
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.redis import get_redis_client
import redis


@pytest.fixture
def client():
    """測試客戶端"""
    return TestClient(app)


@pytest.fixture
def redis_client():
    """Redis 客戶端（測試用）"""
    return get_redis_client()


@pytest.fixture(autouse=True)
def cleanup_redis(redis_client):
    """每個測試後清理 Redis"""
    yield
    # 清理測試資料
    keys = redis_client.keys("test:*")
    if keys:
        redis_client.delete(*keys)
    keys = redis_client.keys("product:*")
    if keys:
        redis_client.delete(*keys)
    keys = redis_client.keys("queue:*")
    if keys:
        redis_client.delete(*keys)
    keys = redis_client.keys("session:*")
    if keys:
        redis_client.delete(*keys)
