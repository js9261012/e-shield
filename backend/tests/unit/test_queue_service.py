"""
佇列服務單元測試
"""
import pytest
import time
from app.services.queue_service import QueueService
from app.core.redis import get_redis_client


class TestQueueService:
    """佇列服務測試"""
    
    def test_join_waiting_queue(self, redis_client):
        """測試加入排隊區"""
        product_id = "1"
        session_id = "test_session_1"
        
        position = QueueService.join_waiting_queue(product_id, session_id)
        
        assert position == 0
        
        waiting_key = f"queue:waiting:product:{product_id}"
        score = redis_client.zscore(waiting_key, session_id)
        assert score is not None
    
    def test_queue_order(self, redis_client):
        """測試佇列順序"""
        product_id = "1"
        
        session1 = "session_1"
        time.sleep(0.001)  # 確保時間戳不同
        session2 = "session_2"
        time.sleep(0.001)
        session3 = "session_3"
        
        pos1 = QueueService.join_waiting_queue(product_id, session1)
        pos2 = QueueService.join_waiting_queue(product_id, session2)
        pos3 = QueueService.join_waiting_queue(product_id, session3)
        
        assert pos1 < pos2 < pos3
    
    def test_move_to_active(self, redis_client):
        """測試從排隊區移入搖滾區"""
        product_id = "1"
        
        for i in range(5):
            QueueService.join_waiting_queue(product_id, f"session_{i}")
        
        moved = QueueService.move_to_active(product_id, count=3)
        
        assert moved == 3
        
        active_count = QueueService.get_active_count(product_id)
        assert active_count == 3
        
        waiting_count = QueueService.get_waiting_count(product_id)
        assert waiting_count == 2
    
    def test_get_positions(self, redis_client):
        """測試查詢位置"""
        product_id = "1"
        session_id = "test_session"
        
        QueueService.join_waiting_queue(product_id, session_id)
        
        waiting_pos = QueueService.get_waiting_position(product_id, session_id)
        assert waiting_pos == 0
        
        active_pos = QueueService.get_active_position(product_id, session_id)
        assert active_pos is None
