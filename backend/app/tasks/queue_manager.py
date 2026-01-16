"""
佇列管理後台任務
定期從 queue:waiting 移入 queue:active
"""
import asyncio
import logging
from app.services.queue_service import QueueService
from app.services.product_service import ProductService

logger = logging.getLogger(__name__)


async def queue_manager_task():
    """佇列管理任務：定期從排隊區移入搖滾區，移除超時使用者"""
    import time
    from app.core.redis import get_redis_client
    from app.services.session_service import SessionService
    
    while True:
        try:
            products = ProductService.get_all_products()
            redis_client = get_redis_client()
            current_time = int(time.time() * 1000)
            
            for product in products:
                active_key = f"queue:active:product:{product.id}"
                active_members = redis_client.zrange(active_key, 0, -1, withscores=True)
                removed_count = 0
                
                for member, score in active_members:
                    session_id = member
                    time_in_active = current_time - int(score)
                    max_time_in_active = 2 * 60 * 1000
                    
                    if time_in_active > max_time_in_active:
                        logger.info(f"商品 {product.id}: 使用者 {session_id} 在搖滾區超過 2 分鐘未購買，自動移除")
                        QueueService.remove_from_active(product.id, session_id)
                        SessionService.update_session(
                            session_id,
                            queue_status="expired"
                        )
                        removed_count += 1
                
                if removed_count > 0:
                    logger.info(f"商品 {product.id}: 移除了 {removed_count} 位超過時限的使用者")
                
                moved_count = QueueService.move_to_active(product.id)
                
                if moved_count > 0:
                    logger.info(f"商品 {product.id}: 從排隊區移入 {moved_count} 人到搖滾區")
            
            await asyncio.sleep(3)
            
        except Exception as e:
            logger.error(f"佇列管理任務錯誤: {str(e)}")
            await asyncio.sleep(3)


def start_queue_manager():
    """啟動佇列管理任務"""
    import asyncio
    loop = asyncio.get_event_loop()
    loop.create_task(queue_manager_task())
