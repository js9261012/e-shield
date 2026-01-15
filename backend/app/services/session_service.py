"""
會話服務
"""
import uuid
from typing import Optional
from app.core.redis import get_redis_client
from app.models.session import Session


class SessionService:
    """會話服務類別"""
    
    @staticmethod
    def _get_session_key(session_id: str) -> str:
        """取得會話 Redis key"""
        return f"session:{session_id}"
    
    @staticmethod
    def create_session(turnstile_verified: bool = False) -> str:
        """
        建立新會話
        
        Args:
            turnstile_verified: Turnstile 驗證狀態
            
        Returns:
            str: 會話 ID
        """
        session_id = str(uuid.uuid4())
        redis_client = get_redis_client()
        session_key = SessionService._get_session_key(session_id)
        
        import time
        current_timestamp = int(time.time() * 1000)
        
        # 建立會話資料
        session_data = {
            "turnstile_verified": "true" if turnstile_verified else "false",
            "verified_at": str(current_timestamp) if turnstile_verified else "",
            "queue_status": "waiting"
        }
        
        redis_client.hset(session_key, mapping=session_data)
        redis_client.expire(session_key, 86400)  # 24 小時過期
        
        return session_id
    
    @staticmethod
    def get_session(session_id: str) -> Optional[Session]:
        """取得會話資訊"""
        redis_client = get_redis_client()
        session_key = SessionService._get_session_key(session_id)
        
        if not redis_client.exists(session_key):
            return None
        
        session_data = redis_client.hgetall(session_key)
        
        return Session(
            session_id=session_id,
            turnstile_verified=session_data.get("turnstile_verified", "false") == "true",
            verified_at=int(session_data.get("verified_at", 0)) if session_data.get("verified_at") else None,
            queue_position_waiting=int(session_data.get("queue_position_waiting", -1)) if session_data.get("queue_position_waiting") else None,
            queue_position_active=int(session_data.get("queue_position_active", -1)) if session_data.get("queue_position_active") else -1,
            queue_status=session_data.get("queue_status", "waiting"),
            product_id=session_data.get("product_id"),
            purchase_ready_at=int(session_data.get("purchase_ready_at", 0)) if session_data.get("purchase_ready_at") else None,
            purchase_timeout_at=int(session_data.get("purchase_timeout_at", 0)) if session_data.get("purchase_timeout_at") else None
        )
    
    @staticmethod
    def update_session(session_id: str, **kwargs):
        """更新會話資訊"""
        redis_client = get_redis_client()
        session_key = SessionService._get_session_key(session_id)
        
        if not redis_client.exists(session_key):
            return
        
        # 轉換值為字串
        update_data = {k: str(v) if v is not None else "" for k, v in kwargs.items()}
        redis_client.hset(session_key, mapping=update_data)
