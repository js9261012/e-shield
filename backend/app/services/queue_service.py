"""
佇列服務
"""
import time
from typing import Optional, Tuple
from app.core.redis import get_redis_client


class QueueService:
    """佇列服務類別"""
    
    ACTIVE_QUEUE_MAX_SIZE = 10
    
    @staticmethod
    def _get_waiting_key(product_id: str) -> str:
        """取得排隊區 Redis key"""
        return f"queue:waiting:product:{product_id}"
    
    @staticmethod
    def _get_active_key(product_id: str) -> str:
        """取得搖滾區 Redis key"""
        return f"queue:active:product:{product_id}"
    
    @staticmethod
    def join_waiting_queue(product_id: str, session_id: str) -> int:
        """
        加入排隊區
        
        Returns:
            int: 在排隊區的位置（0-based）
        """
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"使用者 {session_id} 加入商品 {product_id} 的排隊區")
        
        redis_client = get_redis_client()
        waiting_key = QueueService._get_waiting_key(product_id)
        current_timestamp = int(time.time() * 1000)
        
        redis_client.zadd(waiting_key, {session_id: current_timestamp})
        position = redis_client.zrank(waiting_key, session_id)
        return position if position is not None else -1
    
    @staticmethod
    def get_waiting_position(product_id: str, session_id: str) -> Optional[int]:
        """查詢在排隊區的位置"""
        redis_client = get_redis_client()
        waiting_key = QueueService._get_waiting_key(product_id)
        
        position = redis_client.zrank(waiting_key, session_id)
        return position if position is not None else None
    
    @staticmethod
    def get_active_position(product_id: str, session_id: str) -> Optional[int]:
        """查詢在搖滾區的位置"""
        redis_client = get_redis_client()
        active_key = QueueService._get_active_key(product_id)
        
        position = redis_client.zrank(active_key, session_id)
        return position if position is not None else None
    
    @staticmethod
    def get_waiting_count(product_id: str) -> int:
        """取得排隊區總人數"""
        redis_client = get_redis_client()
        waiting_key = QueueService._get_waiting_key(product_id)
        return redis_client.zcard(waiting_key)
    
    @staticmethod
    def get_active_count(product_id: str) -> int:
        """取得搖滾區總人數"""
        redis_client = get_redis_client()
        active_key = QueueService._get_active_key(product_id)
        return redis_client.zcard(active_key)
    
    @staticmethod
    def move_to_active(product_id: str, count: int = None) -> int:
        """
        從排隊區移入搖滾區
        
        Args:
            product_id: 商品 ID
            count: 要移入的人數（預設為填滿搖滾區）
            
        Returns:
            int: 實際移入的人數
        """
        redis_client = get_redis_client()
        waiting_key = QueueService._get_waiting_key(product_id)
        active_key = QueueService._get_active_key(product_id)
        
        current_active_count = QueueService.get_active_count(product_id)
        available_slots = QueueService.ACTIVE_QUEUE_MAX_SIZE - current_active_count
        
        if available_slots <= 0:
            return 0
        
        move_count = count if count is not None else available_slots
        move_count = min(move_count, available_slots)
        
        if move_count <= 0:
            return 0
        
        members = redis_client.zrange(waiting_key, 0, move_count - 1, withscores=True)
        
        if not members:
            return 0
        
        current_timestamp = int(time.time() * 1000)
        moved_count = 0
        pipe = redis_client.pipeline()
        moved_sessions = []
        
        for member, score in members:
            session_id = member
            pipe.zadd(active_key, {session_id: current_timestamp})
            pipe.zrem(waiting_key, session_id)
            moved_sessions.append(session_id)
            moved_count += 1
        
        pipe.execute()
        
        if moved_sessions:
            from app.services.session_service import SessionService
            for session_id in moved_sessions:
                position = redis_client.zrank(active_key, session_id)
                SessionService.update_session(
                    session_id,
                    queue_position_active=position if position is not None else -1,
                    queue_position_waiting=None,
                    queue_status="active"
                )
        
        return moved_count
    
    @staticmethod
    def remove_from_active(product_id: str, session_id: str):
        """從搖滾區移除"""
        redis_client = get_redis_client()
        active_key = QueueService._get_active_key(product_id)
        redis_client.zrem(active_key, session_id)
        
        lock_key = f"purchase:lock:{session_id}"
        redis_client.delete(lock_key)
    
    @staticmethod
    def estimate_wait_time(product_id: str, position_waiting: int, position_active: int) -> int:
        """
        預估等待時間（秒）
        
        Args:
            product_id: 商品 ID
            position_waiting: 在排隊區的位置
            position_active: 在搖滾區的位置
            
        Returns:
            int: 預估等待時間（秒）
        """
        if position_active >= 0:
            return position_active * 30
        
        if position_waiting >= 0:
            active_count = QueueService.get_active_count(product_id)
            waiting_ahead = position_waiting
            time_to_active = (waiting_ahead // QueueService.ACTIVE_QUEUE_MAX_SIZE) * 10
            time_in_active = QueueService.ACTIVE_QUEUE_MAX_SIZE * 30
            return time_to_active + time_in_active
        
        return 0
